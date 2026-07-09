import logging
import os
from pathlib import Path

from django.conf import settings
from django_q.models import Schedule
from django_q.tasks import schedule
from openfoodfacts import Flavor

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.api.prices.serializers import PriceSerializer
from open_prices.api.proofs.serializers import ProofSerializer
from open_prices.badges.models import Badge
from open_prices.challenges.models import Challenge
from open_prices.common.history import history_clean_duplicate_command
from open_prices.common.openfoodfacts import import_product_db
from open_prices.common.utils import export_model_to_jsonl_gz
from open_prices.locations.models import Location
from open_prices.moderation import rules as moderation_rules
from open_prices.moderation.rules import create_flags_from_price_outliers
from open_prices.prices.models import Price, PriceStatistics5y
from open_prices.products.models import Product
from open_prices.proofs.models import Proof
from open_prices.stats.models import TotalStats
from open_prices.users.models import User

logger = logging.getLogger(__name__)


def import_off_db_task():
    if settings.ENABLE_IMPORT_OFF_DB_TASK is True:
        import_product_db(flavor=Flavor.off)
        import_product_db(flavor=Flavor.off, obsolete=True)


def import_obf_db_task():
    if settings.ENABLE_IMPORT_OBF_DB_TASK is True:
        import_product_db(flavor=Flavor.obf)


def import_opff_db_task():
    if settings.ENABLE_IMPORT_OPFF_DB_TASK is True:
        import_product_db(flavor=Flavor.opff)


def import_opf_db_task():
    if settings.ENABLE_IMPORT_OPF_DB_TASK is True:
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
    TotalStats.update_task()


def update_product_counts_task():
    Product.update_task()


def update_user_counts_task():
    User.update_task()


def update_location_counts_task():
    Location.update_task()


def update_challenge_task():
    Challenge.update_task()


def update_badge_task():
    Badge.update_task()
    User.update_badge_count_task()


def fix_proof_fields_task():
    """
    Proofs uploaded via the (old) mobile app lack location/date/currency fields
    Fill these fields using the proof's prices
    """
    for proof in Proof.objects.with_stats().filter(
        price_count_annotated__gte=1, location=None
    ):
        proof.set_missing_fields_from_prices()


def moderation_tasks():
    moderation_rules.cleanup_products_with_long_barcodes()
    moderation_rules.cleanup_products_with_invalid_barcodes()


def dump_db_task():
    """
    Dump the database as JSONL files to the data directory
    """
    output_dir = Path(os.path.join(settings.BASE_DIR, "data"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for table_name, model_class, schema_class in (
        ("prices", Price, PriceSerializer),
        ("proofs", Proof, ProofSerializer),
        ("locations", Location, LocationSerializer),
    ):
        export_model_to_jsonl_gz(table_name, model_class, schema_class, output_dir)


def proof_draft_cleanup_task():
    """
    Delete draft proofs older than 1 hour.
    """
    deleted_count, _ = Proof.all_objects.draft_to_delete().delete()
    logger.info(f"Deleted {deleted_count} draft proofs")


def history_cleanup_task():
    history_clean_duplicate_command()


def create_flags_from_price_outliers_and_update_view():
    """Create flag associated with detected price outliers, for prices that were
    created the day before.
    Then refresh the `price_statistics_5y` materialized view."""
    logger.info("Running create_flags_from_price_outliers task")
    create_flags_from_price_outliers()
    logger.info("Refreshing materialized view...")
    PriceStatistics5y.refresh_materialized_view()


CRON_SCHEDULES = {
    "import_obf_db_task": ("0 15 * * *", {}),  # daily at 15:00
    "import_opff_db_task": ("10 15 * * *", {}),  # daily at 15:10
    "import_opf_db_task": ("20 15 * * *", {}),  # daily at 15:20
    "import_off_db_task": ("30 15 * * *", {}),  # daily at 15:30
    "dump_db_task": ("0 23 * * *", {}),  # daily at 23:00
    "fix_proof_fields_task": ("0 1 * * *", {}),  # daily at 01:00
    "moderation_tasks": ("10 1 * * *", {}),  # daily at 01:10
    "history_cleanup_task": ("20 1 * * *", {}),  # daily at 01:20
    "create_flags_from_price_outliers_and_update_view": (  # daily at 00:30
        "30 0 * * *",
        {},
    ),
    "update_challenge_task": ("30 1 * * *", {}),  # daily at 01:30
    "update_user_counts_task": ("0 2 * * *", {}),  # daily at 02:00
    "update_badge_task": ("5 2 * * *", {}),  # daily at 02:05
    "update_total_stats_task": ("10 2 * * *", {}),  # daily at 02:10
    "update_location_counts_task": (
        "20 2 * * 1",  # every start of the week (at 02:20)
        {},
    ),
    "update_product_counts_task": (
        "30 2 * * 1",  # every start of the week (at 02:30)
        {"timeout": 10 * 60 * 60},  # 10 hours
    ),
    "proof_draft_cleanup_task": ("*/5 * * * *", {}),  # every 5 minutes
}

for task_name, (task_cron, q_options) in CRON_SCHEDULES.items():
    if not Schedule.objects.filter(name=task_name).exists():
        schedule(
            f"open_prices.common.tasks.{task_name}",
            name=task_name,
            schedule_type=Schedule.CRON,
            cron=task_cron,
            **q_options,
        )
        print(f"Task {task_name} scheduled with cron {task_cron}")
