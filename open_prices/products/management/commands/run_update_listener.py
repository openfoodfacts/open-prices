import datetime
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from openfoodfacts import Flavor
from openfoodfacts.redis import ProductUpdateEvent
from openfoodfacts.redis import UpdateListener as BaseUpdateListener
from openfoodfacts.redis import get_redis_client
from openfoodfacts.utils import get_logger

from open_prices.products.tasks import process_delete, process_update

logger = get_logger()


class UpdateListener(BaseUpdateListener):
    def process_redis_update(self, redis_update: ProductUpdateEvent):
        logger.debug("New update: %s", redis_update)

        if redis_update.product_type == "food":
            flavor = Flavor.off
        elif redis_update.product_type == "beauty":
            flavor = Flavor.obf
        elif redis_update.product_type == "petfood":
            flavor = Flavor.opff
        elif redis_update.product_type == "product":
            flavor = Flavor.opf
        else:
            raise ValueError(
                f"no Flavor matched for product_type {redis_update.product_type}"
            )
        if redis_update.action == "deleted":
            logger.info("Product %s has been deleted", redis_update.code)
            process_delete(redis_update.code, flavor)
        elif redis_update.action == "updated":
            now = datetime.datetime.now(datetime.timezone.utc)
            # Often, we receive information through Redis before the info is
            # available through the Product Opener API. We wait 2s to avoid
            # getting out-of-date info.
            if now - redis_update.timestamp < datetime.timedelta(seconds=2):
                logger.debug(
                    "Product %s has been updated less than 2s ago, sleeping 2s before processing",
                    redis_update.code,
                )
                time.sleep(2)
            process_update(redis_update.code, flavor)


class Command(BaseCommand):
    help = """Run a daemon that listens to product updates from Open Food Facts from a Redis stream."""

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write("Launching the update listener...")

        if settings.ENABLE_REDIS_UPDATES is False:
            self.stdout.write("Redis updates are disabled, waiting forever...")

            while True:
                time.sleep(60)

        redis_client = get_redis_client(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT
        )
        listener = UpdateListener(
            redis_client=redis_client,
            redis_latest_id_key=settings.REDIS_LATEST_ID_KEY,
            product_updates_stream_name=settings.REDIS_PRODUCT_UPDATES_STREAM_NAME,
        )
        listener.run()
