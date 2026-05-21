# Core

The Open Prices core is built around a few key objects:

- `Proof`: the source evidence (receipt, shelf image, etc.)
- `Price`: one price extracted or entered from a proof
- `Location`: where the price was observed (physical shop or online)
- `Product`: the linked product or category context

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

Step-by-step usage is documented in [Guides](../guides/README.md).

From a technical point of view, all workflows eventually write into the same core entities (`Proof`, `Price`, `Location`, `Product`), which keeps stats, moderation, and reuse features coherent.
