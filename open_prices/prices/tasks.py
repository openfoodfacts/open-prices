from open_prices.prices.models import Price


def update_tags(price: Price):
    price.update_tags()
