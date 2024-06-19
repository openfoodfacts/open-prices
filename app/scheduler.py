import datetime
import shutil
from pathlib import Path

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from openfoodfacts import Flavor
from openfoodfacts.utils import get_logger

from app.config import settings
from app.db import session
from app.tasks import dump_db, import_product_db

logger = get_logger(__name__)


def import_product_db_job() -> None:
    for flavor in [Flavor.off, Flavor.obf, Flavor.opff, Flavor.opf]:
        # launch a new db session for each flavor
        # to avoid duplicate code errors
        db = session()
        # import the products
        import_product_db(db=db, flavor=flavor)


def dump_db_job() -> None:
    """Dump the database as JSONL files to the data directory."""
    # Create a temporary directory to store the dump
    tmp_dir = Path(f"/tmp/dump-{datetime.datetime.now().isoformat()}").resolve()

    with session() as db:
        dump_db(db, tmp_dir)

    for file_path in tmp_dir.iterdir():
        # Move the file to the final location
        logger.info(f"Moving {file_path} to {settings.data_dir}")
        shutil.move(file_path, settings.data_dir / file_path.name)
    tmp_dir.rmdir()


def run() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_executor(ThreadPoolExecutor(20))
    scheduler.add_jobstore(MemoryJobStore())
    scheduler.add_job(
        import_product_db_job, "cron", max_instances=1, hour=15, minute=0, jitter=60
    )
    scheduler.add_job(
        dump_db_job, "cron", max_instances=1, hour=23, minute=0, jitter=60
    )
    scheduler.start()
