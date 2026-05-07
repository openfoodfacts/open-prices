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

- Make sure you comply with the OdBL licence, mentioning the source of your data, and ensuring to avoid combining non free data you can't release legally as open data. Another requirement is contributing back any product you add using this SDK.

## Reuse

- Please get in touch at reuse@openfoodfacts.org
- We are very interested in learning what the Open Prices data is used for. It is not mandatory, but we would very much appreciate it if you tell us about your re-uses (https://forms.gle/hwaeqBfs8ywwhbTg8) so that we can share them with the Open Food Facts community. And we would be happy to feature it here: [https://prices.openfoodfacts.org/community](https://prices.openfoodfacts.org/community)
