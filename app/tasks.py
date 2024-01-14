import datetime

import tqdm
from openfoodfacts import DatasetType, Flavor, ProductDataset
from openfoodfacts.types import JSONType
from openfoodfacts.utils import get_logger
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import crud
from app.models import Product
from app.schemas import LocationCreate, PriceBase, ProductCreate, UserBase
from app.utils import (
    OFF_FIELDS,
    fetch_location_openstreetmap_details,
    fetch_product_openfoodfacts_details,
    generate_openfoodfacts_main_image_url,
    normalize_product_fields,
)

logger = get_logger(__name__)


# Users
# ------------------------------------------------------------------------------
def increment_user_price_count(db: Session, user: UserBase):
    crud.increment_user_price_count(db, user=user)


# Products
# ------------------------------------------------------------------------------
def create_price_product(db: Session, price: PriceBase):
    # The price may not have a product code, if it's the price of a
    # barcode-less product
    if price.product_code:
        # get or create the corresponding product
        product = ProductCreate(code=price.product_code)
        db_product, created = crud.get_or_create_product(
            db, product=product, init_price_count=1
        )
        # link the product to the price
        crud.link_price_product(db, price=price, product=db_product)
        # fetch data from OpenFoodFacts if created
        if created:
            product_openfoodfacts_details = fetch_product_openfoodfacts_details(
                product=db_product
            )
            if product_openfoodfacts_details:
                crud.update_product(
                    db, product=db_product, update_dict=product_openfoodfacts_details
                )
        else:
            # Increment the price count of the product
            crud.increment_product_price_count(db, product=db_product)


def import_product_db(db: Session, batch_size: int = 1000):
    """Import from DB JSONL dump to insert/update product table.

    :param db: the session to use
    :param batch_size: the number of products to insert/update in a single
      transaction, defaults to 1000
    """
    logger.info("Launching import_product_db")
    existing_codes = set(db.execute(select(Product.code)).scalars())
    logger.info("Number of existing codes: %d", len(existing_codes))
    dataset = ProductDataset(
        dataset_type=DatasetType.jsonl, force_download=True, download_newer=True
    )

    added_count = 0
    updated_count = 0
    buffer_len = 0
    # the dataset was created after the start of the day, every product updated
    # after should be skipped, as we don't know the exact creation time of the
    # dump
    start_datetime = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        hour=0, minute=0, second=0
    )
    seen_codes = set()
    for product in tqdm.tqdm(dataset):
        if "code" not in product:
            continue

        product_code = product["code"]
        # Some products are duplicated in the dataset, we skip them
        if product_code in seen_codes:
            continue
        seen_codes.add(product_code)
        images: JSONType = product.get("images", {})
        last_modified_t = product.get("last_modified_t")
        last_modified = (
            datetime.datetime.fromtimestamp(last_modified_t, tz=datetime.timezone.utc)
            if last_modified_t
            else None
        )

        if last_modified is None:
            continue

        # Skip products that have been modified today (more recent updates are
        # possible)
        if last_modified >= start_datetime:
            logger.debug("Skipping %s", product_code)
            continue

        if product_code not in existing_codes:
            item = {"code": product_code, "source": Flavor.off}
            for key in OFF_FIELDS:
                item[key] = product[key] if key in product else None

            item = normalize_product_fields(item)
            item["image_url"] = generate_openfoodfacts_main_image_url(
                product_code, images, product["lang"]
            )
            db.add(Product(**item))
            added_count += 1
            buffer_len += 1

        else:
            item = {key: product[key] if key in product else None for key in OFF_FIELDS}
            item["image_url"] = generate_openfoodfacts_main_image_url(
                product_code, images, product["lang"]
            )
            item = normalize_product_fields(item)
            execute_result = db.execute(
                Product.__table__.update()
                .where(Product.code == product_code)
                .where(Product.source == Flavor.off)
                # Update the product if only if it has not been updated since
                # the creation of the current dataset
                .where(
                    or_(
                        Product.updated < last_modified,
                        Product.updated == None,  # noqa: E711, E501
                    )
                )
                .values(**item)
            )
            updated_count += execute_result.rowcount
            buffer_len += 1

        if buffer_len % batch_size == 0:
            db.commit()
            logger.info(f"Products: {added_count} added, {updated_count} updated")
            buffer_len = 0


# Locations
# ------------------------------------------------------------------------------
def create_price_location(db: Session, price: PriceBase):
    if price.location_osm_id and price.location_osm_type:
        # get or create the corresponding location
        location = LocationCreate(
            osm_id=price.location_osm_id, osm_type=price.location_osm_type
        )
        db_location, created = crud.get_or_create_location(
            db, location=location, init_price_count=1
        )
        # link the location to the price
        crud.set_price_location(db, price=price, location=db_location)
        # fetch data from OpenStreetMap if created
        if created:
            location_openstreetmap_details = fetch_location_openstreetmap_details(
                location=db_location
            )
            if location_openstreetmap_details:
                crud.update_location(
                    db, location=db_location, update_dict=location_openstreetmap_details
                )
        else:
            # Increment the price count of the location
            crud.increment_location_price_count(db, location=db_location)
