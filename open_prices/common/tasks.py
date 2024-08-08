import os
from pathlib import Path

from django.conf import settings
from django_q.models import Schedule
from django_q.tasks import schedule
from openfoodfacts import Flavor

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.api.prices.serializers import PriceSerializer
from open_prices.api.proofs.serializers import ProofSerializer
from open_prices.common.openfoodfacts import import_product_db
from open_prices.common.utils import export_model_to_jsonl_gz
from open_prices.locations.models import Location
from open_prices.prices.models import Price
from open_prices.proofs.models import Proof


def import_product_db_task():
    for flavor in [Flavor.off, Flavor.obf, Flavor.opff, Flavor.opf]:
        import_product_db(flavor=flavor)


def dump_db_task():
    output_dir = Path(os.path.join(settings.BASE_DIR, "static/data"))

    for table_name, model_class, schema_class in (
        ("prices", Price, PriceSerializer),
        ("proofs", Proof, ProofSerializer),
        ("locations", Location, LocationSerializer),
    ):
        export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir)


# sync product database with Open Food Facts daily at 15:00
# https://cron.help/#0_15_*_*_*
schedule(
    "open_prices.common.tasks.import_product_db_task",
    name="import_product_db_task",
    schedule_type=Schedule.CRON,
    cron="0 15 * * *",
)

# dump the database as JSONL files to the data directory daily at 23:00
# https://cron.help/#0_23_*_*_*
schedule(
    "open_prices.common.tasks.dump_db_task",
    name="dump_db_task",
    schedule_type=Schedule.CRON,
    cron="0 23 * * *",
)
