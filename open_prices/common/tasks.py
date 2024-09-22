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
from open_prices.users.models import User


def import_product_db_task():
    """
    Sync product database with Open Food Facts
    """
    for flavor in [Flavor.off, Flavor.obf, Flavor.opff, Flavor.opf]:
        import_product_db(flavor=flavor)


def update_user_counts_task():
    """
    Update all user price_counts
    """
    for user in User.objects.all():
        for field in User.COUNT_FIELDS:
            getattr(user, f"update_{field}")()


def dump_db_task():
    """
    Dump the database as JSONL files to the data directory
    """
    output_dir = Path(os.path.join(settings.BASE_DIR, "static/data"))

    for table_name, model_class, schema_class in (
        ("prices", Price, PriceSerializer),
        ("proofs", Proof, ProofSerializer),
        ("locations", Location, LocationSerializer),
    ):
        export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir)


CRON_SCHEDULES = {
    "import_product_db_task": "0 15 * * *",  # daily at 15:00
    "update_user_counts_task": "0 2 * * 1",  # every start of the week
    "dump_db_task": "0 23 * * *",  # daily at 23:00
}

for task_name, task_cron in CRON_SCHEDULES.items():
    if not Schedule.objects.filter(name=task_name).exists():
        schedule(
            f"open_prices.common.tasks.{task_name}",
            name=task_name,
            schedule_type=Schedule.CRON,
            cron=task_cron,
        )
        print(f"Task {task_name} scheduled with cron {task_cron}")
