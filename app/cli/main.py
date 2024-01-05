import typer

app = typer.Typer()


@app.command()
def import_product_db() -> None:
    """Import from DB JSONL dump to insert/update product table."""
    from app.db import session
    from app.tasks import import_product_db
    from app.utils import get_logger

    get_logger()
    db = session()
    import_product_db(db)


@app.command()
def run_scheduler() -> None:
    """Launch the scheduler."""
    from app import scheduler
    from app.utils import get_logger

    get_logger()
    scheduler.run()


def main() -> None:
    app()
