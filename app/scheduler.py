from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from openfoodfacts import Flavor
from openfoodfacts.utils import get_logger

from app.db import session
from app.tasks import import_product_db

logger = get_logger(__name__)


def import_product_db_job() -> None:
    db = session()
    import_product_db(db=db, flavor=Flavor.off)  # Open Food Facts
    import_product_db(db=db, flavor=Flavor.obf)  # Open Beauty Facts
    import_product_db(db=db, flavor=Flavor.opff)  # Open Pet Food Facts
    import_product_db(db=db, flavor=Flavor.opf)  # Open Products Facts


def run() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_executor(ThreadPoolExecutor(20))
    scheduler.add_jobstore(MemoryJobStore())
    scheduler.add_job(
        import_product_db_job, "cron", max_instances=1, hour=10, minute=0, jitter=60
    )
    scheduler.start()
