# Open Food Facts (Product data)

Open Prices relies on Open Food Facts product data to enrich and validate prices.

## What is reused

Open Prices reuses product information such as:

- product codes and product names
- brands and categories
- taxonomy data (for categories and related matching)

## Why it matters

This integration makes contribution and analysis easier:

- contributors can link prices to existing products
- category-based flows are more robust
- challenge and stats logic can reuse shared taxonomy concepts

## Data sync and freshness

Open Prices regularly imports product data from Open Food Facts flavors. This allows product lookup and enrichment to stay reasonably up to date.

Operational details (tasks, deployment, scripts) are summarized in the project wiki and backend task configuration.
