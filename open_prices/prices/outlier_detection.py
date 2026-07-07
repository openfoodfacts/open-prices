import datetime

from open_prices.prices.constants import TYPE_CATEGORY, TYPE_PRODUCT
from open_prices.prices.models import Price


def find_outliers(
    target_date: datetime.date | None = None,
    median_threshold: int = 3,
    min_count: int = 3,
):
    """Find price outliers based on the median of other prices.

    Outliers are defined as prices that are greater than `median_threshold` times
    the median of the group or less than the median of the group divided by
    `median_threshold`.

    We compare each price with a group of prices that have the same:

    - `product_code` (for product type) or `category_tag` (for category type)
    - `osm_address_country_code`
    - `price_per`
    - `type`
    - `currency`

    We run the query for each product type (product and category) and join the
    results to find outliers.

    :param target_date: The date to find outliers for, or None to find outliers for
        all dates.
    :param median_threshold: The threshold for detecting outliers. Prices that are
        greater than `median_threshold` times the median or less than the median
        divided by `median_threshold` are considered outliers.
    :param min_count: The minimum number of prices required to calculate the median.
    :return: A list of outliers, as Price objects. Each Price object has additional
        fields `median` and `count`, which indicate the median price for the group and
        the number of prices used to calculate it respectively.
    """
    queries = []
    for product_type in [TYPE_PRODUCT, TYPE_CATEGORY]:
        code_field = "product_code" if product_type == TYPE_PRODUCT else "category_tag"
        # A few explanations on this query:
        # - we use `COALESCE(t1.price_per, '')` so that `t1.price_per = t2.price_per`
        #   is evaluated as true when both fields are null
        # - `t2.stddev > 0` clause is added to avoid considering a price an outlier
        #   when all the other prices are the same (i.e. stddev is 0)
        # - `t2.count >= min_count` clause is added to avoid considering a price an outlier
        #   when there are not enough other prices to calculate a meaningful median
        query = f"""
            SELECT
                t1.id,
                t1.product_code,
                t1.category_tag,
                t1.type,
                t1.price_per,
                t1.price,
                t2.median,
                t2.count
            FROM prices AS t1
            JOIN price_statistics_5y AS t2
                ON (t1.{code_field} = t2.code AND
                    t1.currency = t2.currency AND
                    t1.type = t2.type AND
                    COALESCE(t1.price_per, '') = COALESCE(t2.price_per, ''))
            JOIN locations AS t3 ON (t1.location_id = t3.id)
            WHERE
                t1.type = '{product_type}' AND
                t2.osm_address_country_code = t3.osm_address_country_code AND (
                    (t1.price >= (%(median_threshold)s * t2.median))
                    OR (t1.price <= (t2.median / %(median_threshold)s))
                ) AND
                t2.stddev > 0 AND
                t2.count >= %(min_count)s AND
                (%(target_date)s IS NULL OR t1.created::date = %(target_date)s)
        """
        queries.append(query)

    full_query = f"({queries[0]}) UNION ({queries[1]})"
    return Price.objects.raw(
        full_query,
        {
            "median_threshold": median_threshold,
            "min_count": min_count,
            "target_date": target_date,
        },
    )
