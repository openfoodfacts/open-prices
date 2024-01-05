from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from openfoodfacts.utils import get_logger

from app.db import session
from app.tasks import import_product_db

logger = get_logger(__name__)


def import_product_db_job():
    db = session()
    import_product_db(db=db)


def run():
    scheduler = BlockingScheduler()
    scheduler.add_executor(ThreadPoolExecutor(20))
    scheduler.add_jobstore(MemoryJobStore())
    scheduler.add_job(
        import_product_db_job, "cron", max_instances=1, hour=6, minute=0, jitter=60
    )
    scheduler.start()
