import datetime
import gzip
from pathlib import Path

import tqdm
from openfoodfacts import DatasetType, Flavor, ProductDataset
from openfoodfacts.types import JSONType
from openfoodfacts.utils import get_logger
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models import Location, Price, Product, Proof
from app.schemas import LocationCreate, ProductCreate, UserCreate
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
def increment_user_price_count(db: Session, user: UserCreate) -> None:
    crud.increment_user_price_count(db, user=user)


# Proofs
# ------------------------------------------------------------------------------
def increment_proof_price_count(db: Session, proof: Proof) -> None:
    crud.increment_proof_price_count(db, proof=proof)


# Products
# ------------------------------------------------------------------------------
def create_price_product(db: Session, price: Price) -> None:
    # The price may not have a product code, if it's the price of a
    # barcode-less product
    if price.product_code:
        # get or create the corresponding product
        product = ProductCreate(code=price.product_code, price_count=1)
        db_product, created = crud.get_or_create_product(db, product=product)
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


def import_product_db(
    db: Session, flavor: Flavor = Flavor.off, batch_size: int = 1000
) -> None:
    """Import from DB JSONL dump to insert/update product table.

    :param db: the session to use
    :param batch_size: the number of products to insert/update in a single
      transaction, defaults to 1000
    """
    logger.info(f"Launching import_product_db ({flavor})")
    existing_codes = set(db.execute(select(Product.code)).scalars())
    logger.info("Number of existing codes: %d", len(existing_codes))
    dataset = ProductDataset(
        flavor=flavor,
        dataset_type=DatasetType.jsonl,
        force_download=True,
        download_newer=True,
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
        # Skip products without a code, or with wrong code
        if ("code" not in product) or (not product["code"].isdigit()):
            continue
        product_code = product["code"]

        # Skip duplicate products
        if product_code in seen_codes:
            continue
        seen_codes.add(product_code)

        # Some products have no "lang" field (especially non-OFF products)
        product_lang = product.get("lang", product.get("lc", "en"))
        # Store images & last_modified_t
        product_images: JSONType = product.get("images", {})
        product_last_modified_t = product.get("last_modified_t")

        # Convert last_modified_t to a datetime object
        # (sometimes the field is a string, convert to int first)
        if isinstance(product_last_modified_t, str):
            product_last_modified_t = int(product_last_modified_t)
        product_source_last_modified = (
            datetime.datetime.fromtimestamp(
                product_last_modified_t, tz=datetime.timezone.utc
            )
            if product_last_modified_t
            else None
        )
        # Skip products that have no last_modified date
        if product_source_last_modified is None:
            continue

        # Skip products that have been modified today (more recent updates are
        # possible)
        if product_source_last_modified >= start_datetime:
            logger.debug("Skipping %s", product_code)
            continue

        # Build product dict to insert/update
        product_dict = {
            key: product[key] if (key in product) else None for key in OFF_FIELDS
        }
        product_dict["image_url"] = generate_openfoodfacts_main_image_url(
            product_code, product_images, product_lang, flavor=flavor
        )
        product_dict["source"] = flavor
        product_dict["source_last_synced"] = datetime.datetime.now()
        product_dict = normalize_product_fields(product_dict)

        # Case 1: new OFF product (not in OP database)
        if product_code not in existing_codes:
            product_dict["code"] = product_code
            db.add(Product(**product_dict))
            added_count += 1
            buffer_len += 1

        # Case 2: existing product (already in OP database)
        else:
            execute_result = db.execute(
                update(Product)
                .where(Product.code == product_code)
                # Update the product if it is part of OFF
                # or if it has no source (created in Open Prices before OFF)
                .where(
                    or_(
                        Product.source == flavor,
                        Product.source == None,  # noqa: E711, E501
                    )
                )
                # Update the product if it has not been updated since
                # the creation of the current dataset
                .where(
                    or_(
                        Product.source_last_synced < product_source_last_modified,
                        Product.source_last_synced == None,  # noqa: E711, E501
                    )
                )
                .values(**product_dict)
            )
            updated_count += execute_result.rowcount
            buffer_len += 1

        # update the database regularly
        if buffer_len % batch_size == 0:
            db.commit()
            logger.info(f"Products: {added_count} added, {updated_count} updated")
            buffer_len = 0

    # final database update
    db.commit()
    logger.info(f"Products: {added_count} added, {updated_count} updated. Done!")


# Locations
# ------------------------------------------------------------------------------
def create_price_location(db: Session, price: Price) -> None:
    if price.location_osm_id and price.location_osm_type:
        # get or create the corresponding location
        location = LocationCreate(
            osm_id=price.location_osm_id,
            osm_type=price.location_osm_type,
            price_count=1,
        )
        db_location, created = crud.get_or_create_location(db, location=location)
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


def create_proof_location(db: Session, proof: Proof) -> None:
    if proof.location_osm_id and proof.location_osm_type:
        # get or create the corresponding location
        location = LocationCreate(
            osm_id=proof.location_osm_id,
            osm_type=proof.location_osm_type,
        )
        db_location, created = crud.get_or_create_location(db, location=location)
        # link the location to the proof
        crud.set_proof_location(db, proof=proof, location=db_location)
        # fetch data from OpenStreetMap if created
        if created:
            location_openstreetmap_details = fetch_location_openstreetmap_details(
                location=db_location
            )
            if location_openstreetmap_details:
                crud.update_location(
                    db, location=db_location, update_dict=location_openstreetmap_details
                )
        # else:
        #     # Increment the proof count of the location
        #     crud.increment_location_proof_count(db, location=db_location)


# Other
# ------------------------------------------------------------------------------
def dump_db(db: Session, output_dir: Path) -> None:
    """Dump the database to gzipped JSONL files."""
    logger.info("Creating dumps of the database")
    output_dir.mkdir(parents=True, exist_ok=True)

    for table_name, model_cls, schema_cls in (
        ("prices", Price, schemas.PriceFull),
        ("proofs", Proof, schemas.ProofFull),
        ("locations", Location, schemas.LocationFull),
    ):
        logger.info(f"Dumping {table_name}")
        output_path = output_dir / f"{table_name}.jsonl.gz"
        with gzip.open(output_path, "wt") as f:
            for (item,) in tqdm.tqdm(db.execute(select(model_cls)), desc=table_name):
                f.write(schema_cls(**item.__dict__).model_dump_json())
                f.write("\n")
