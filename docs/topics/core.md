# Core

## Data model

The Open Prices core is built around 4 key objects:

- `Proof`: the source evidence (receipt, shelf image, GDPR import, shop import)
- `Price`: one price extracted or entered from a proof
- `Location`: where the price was observed (physical shop or online)
- `Product`: the linked Open Food Facts product (if barcode) (or category tag if not)

These objects are connected to keep data consistent:

- prices are attached to proofs
- prices and proofs are attached to locations
- prices are linked to products (or category tags)

## Why this model

This model helps Open Prices support:

- manual contributions
- assisted contribution workflows
- API-based contribution from external clients

It also enables quality checks, moderation, and history tracking while keeping the same core structure.

## Contribution workflows

Step-by-step usage (Web frontend, Mobile, API) is documented in [Guides](../guides/README.md).
