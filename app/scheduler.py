from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from openfoodfacts import Flavor
from openfoodfacts.utils import get_logger

from app.db import session
from app.tasks import import_product_db

logger = get_logger(__name__)


def import_product_db_job() -> None:
    for flavor in [Flavor.off, Flavor.obf, Flavor.opff, Flavor.opf]:
        # launch a new db session for each flavor
        # to avoid duplicate code errors
        db = session()
        # import the products
        import_product_db(db=db, flavor=flavor)


def run() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_executor(ThreadPoolExecutor(20))
    scheduler.add_jobstore(MemoryJobStore())
    scheduler.add_job(
        import_product_db_job, "cron", max_instances=1, hour=10, minute=0, jitter=60
    )
    scheduler.start()
