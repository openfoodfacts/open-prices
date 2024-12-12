import logging

from openfoodfacts import Flavor

from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.products.models import Product

logger = logging.getLogger(__name__)


def fetch_and_save_data_from_openfoodfacts(product: Product):
    product_openfoodfacts_details = common_openfoodfacts.get_product_dict(product.code)
    if product_openfoodfacts_details:
        for key, value in product_openfoodfacts_details.items():
            setattr(product, key, value)
        product.save()


def process_update(code: str, flavor: Flavor) -> None:
    """Process an update of a product from Product Opener.

    We update the product table with the latest information from Open Food
    Facts. In case the product does not exist, we create it.

    :param code: The code of the product
    :param flavor: The flavor of the product
    """
    product_openfoodfacts_details = common_openfoodfacts.get_product_dict(code, flavor)

    if product_openfoodfacts_details:
        does_not_exist = False
        try:
            product = Product.objects.get(code=code)
        except Product.DoesNotExist:
            logger.info(
                "Product %s does not exist in the database, cannot update product table",
                code,
            )
            does_not_exist = True

        if does_not_exist:
            product_openfoodfacts_details["code"] = code
            product = Product(**product_openfoodfacts_details)
        else:
            for key, value in product_openfoodfacts_details.items():
                setattr(product, key, value)

        product.save()


def process_delete(code: str, flavor: Flavor):
    try:
        product = Product.objects.get(code=code)
    except Product.DoesNotExist:
        logger.info(
            "Product %s does not exist in the database, cannot delete product table",
            code,
        )
        return

    product.delete()
