# Price outlier detection

To detect erroneous prices, we added an outlier detection system.

The algorithm is simple. We first group all prices per:

- barcode (if `type=PRODUCT`) or category_tag (if `type=CATEGORY`)
- type (`PRODUCT` or `CATEGORY`)
- country code (ex: `FR`)
- price per (`UNIT` or `KILOGRAM`)
- currency code (ex: `EUR`)

and compute the price median for each group.

Let's call `x` the price we want to run the outlier detection algorithm against and `med` the price median of the group associated with the price.

If there are at least 3 prices in the group, and `x` is higher than  `3 * med` or lower than `med / 3`, we classify the price as an outlier.

## Implementation

We create a materialized view that stores statistics about each price group, for all prices in the last 5 years:

```sql
CREATE MATERIALIZED VIEW price_statistics_5y AS (
  SELECT
    t2.osm_address_country_code || '_' || t1.product_code || '_' || t1.price_per || '_' || t1.currency as id,
    t2.osm_address_country_code,
    t1.product_code as code,
    t1.price_per,
    t1.currency,
    'PRODUCT' as type,
    AVG(price) as mean,
    COUNT(*) as count,
    STDDEV(price) as stddev,
    MIN(price) as min,
    MAX(price) as max,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
      ORDER BY
        price
    ) as median
  FROM
    prices as t1
    JOIN locations as t2 on t1.location_id = t2.id
  WHERE
    t1.type = 'PRODUCT'
    AND t1.date >= CURRENT_DATE - (interval '5 years')
  GROUP BY
    t2.osm_address_country_code,
    t1.product_code,
    t1.price_per,
    t1.currency
)
UNION
(
  SELECT
    t2.osm_address_country_code || '_' || t1.category_tag || '_' || t1.price_per || '_' || t1.currency as id,
    t2.osm_address_country_code,
    t1.category_tag as code,
    t1.price_per,
    t1.currency,
    'CATEGORY' as type,
    AVG(price) as mean,
    COUNT(*) as count,
    STDDEV(price) as stddev,
    MIN(price) as min,
    MAX(price) as max,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
      ORDER BY
        price
    ) as median
  FROM
    prices as t1
    JOIN locations as t2 on t1.location_id = t2.id
  WHERE
    t1.type = 'CATEGORY'
    AND t1.date >= CURRENT_DATE - (interval '5 years')
  GROUP BY
    t2.osm_address_country_code,
    t1.category_tag,
    t1.price_per,
    t1.currency
);
```

A 5 year window was added to prevent possible old prices (which are assumed to be much lower due to inflation) to skew the group statistics.

This view contains both product and category price statistics, merged together: we use the `code` field to store the product code or the category tag, depending on the type of price.

Outliers can be detected easily by performing a join between the `price` table and the `price_statistics_5y` view, and filtering for prices that are either greater than `3 * med` or lower than `med / 3`.
