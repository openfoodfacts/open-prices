# API

## Documentation

### Links

- pre-prod: [https://prices.openfoodfacts.net/api/docs](https://prices.openfoodfacts.net/api/docs)
- production: [https://prices.openfoodfacts.org/api/docs](https://prices.openfoodfacts.org/api/docs)

### Environments

We have two environments:

- pre-production: for testing and staging
- production: for the live data. ⚠️ Please test your scripts on pre-production before running them on production.

### Authentication

- Some endpoints require authentication
- You will need to create an account on [Open Food Facts](https://world.openfoodfacts.org). Then generate a `token` through the dedicated Open Prices endpoint.
    - when switching from pre-production to production, the account stays the same, but you will need to generate a new token
- Authentication method: Bearer token in the `Authorization` header

## License

Make sure you comply with the OdBL licence, mentioning the source of your data, and ensuring to avoid combining non free data you can't release legally as open data. Another requirement is contributing back any product you add using this SDK.

## Reuse

see [Reuses](../community/reuses.md)
