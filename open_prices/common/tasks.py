from django_q.models import Schedule
from django_q.tasks import schedule
from openfoodfacts import Flavor

from open_prices.common.openfoodfacts import import_product_db


def import_product_db_task():
    for flavor in [Flavor.off, Flavor.obf, Flavor.opff, Flavor.opf]:
        import_product_db(flavor=flavor)


def dump_db_task():
    pass


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
