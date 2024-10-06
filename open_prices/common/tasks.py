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
from open_prices.products.models import Product
from open_prices.proofs.models import Proof
from open_prices.stats.models import TotalStats
from open_prices.users.models import User


def import_off_db_task():
    import_product_db(flavor=Flavor.off)


def import_obf_db_task():
    import_product_db(flavor=Flavor.obf)


def import_opff_db_task():
    import_product_db(flavor=Flavor.opff)


def import_opf_db_task():
    import_product_db(flavor=Flavor.opf)


def import_all_product_db_task():
    """
    Sync product database with Open Food Facts
    """
    import_off_db_task()
    import_obf_db_task()
    import_opff_db_task()
    import_opf_db_task()


def update_total_stats_task():
    """
    Update all total stats
    """
    total_stats = TotalStats.get_solo()
    total_stats.update_price_stats()
    total_stats.update_product_stats()
    total_stats.update_location_stats()
    total_stats.update_proof_stats()
    total_stats.update_user_stats()


def update_product_counts_task():
    """
    Update all product field counts
    """
    for product in Product.objects.filter(price_count__gte=1):
        for field in Product.COUNT_FIELDS:
            getattr(product, f"update_{field}")()


def update_user_counts_task():
    """
    Update all user field counts
    """
    for user in User.objects.all():
        for field in User.COUNT_FIELDS:
            getattr(user, f"update_{field}")()


def update_location_counts_task():
    """
    Update all location field counts
    """
    for location in Location.objects.all():
        for field in Location.COUNT_FIELDS:
            getattr(location, f"update_{field}")()


def fix_proof_fields_task():
    """
    Proofs uploaded via the (old) mobile app lack location/date/currency fields
    Fix these fields using the proof's prices
    """
    for proof in Proof.objects.filter(price_count__gte=1, location=None):
        proof.set_missing_location_from_prices()
        proof.set_missing_date_from_prices()
        proof.set_missing_currency_from_prices()


def dump_db_task():
    """
    Dump the database as JSONL files to the data directory
    """
    output_dir = Path(os.path.join(settings.BASE_DIR, "static", "data"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for table_name, model_class, schema_class in (
        ("prices", Price, PriceSerializer),
        ("proofs", Proof, ProofSerializer),
        ("locations", Location, LocationSerializer),
    ):
        export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir)


CRON_SCHEDULES = {
    "import_obf_db_task": "0 15 * * *",  # daily at 15:00
    "import_opff_db_task": "10 15 * * *",  # daily at 15:10
    "import_opf_db_task": "20 15 * * *",  # daily at 15:20
    "import_off_db_task": "30 15 * * *",  # daily at 15:30
    "update_total_stats_task": "0 1 * * *",  # daily at 01:00
    "fix_proof_fields_task": "10 1 * * *",  # daily at 01:10
    "update_user_counts_task": "0 2 * * 1",  # every start of the week
    "update_location_counts_task": "10 2 * * 1",  # every start of the week
    "update_product_counts_task": "20 2 * * 1",  # every start of the week
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
