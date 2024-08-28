from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.products.models import Product


def fetch_and_save_data_from_openfoodfacts(product: Product):
    product_openfoodfacts_details = common_openfoodfacts.get_product_dict(product)
    if product_openfoodfacts_details:
        for key, value in product_openfoodfacts_details.items():
            setattr(product, key, value)
        product.save()
