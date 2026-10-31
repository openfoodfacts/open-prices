# Gamification

Open Prices includes gamification mechanisms to encourage and reward contributions.

| Mechanism | When | See |
|---|---|---|
| Challenges | on price creation + daily | [below](#challenges) |
| Badges | daily | [below](#badges) |
| Rankings | daily | [below](#rankings) |

## Challenges 🏆

Challenges are used to focus community effort during a time window.

see [https://prices.openfoodfacts.org/challenges](https://prices.openfoodfacts.org/challenges)

### Configuration

Challenges are created & edited by admins (in the Django admin). A challenge can target:

- specific periods (`start_date` & `end_date`, mandatory once published)
- optionally specific categories (`categories`), e.g. `en:breakfast-cereals`. Their children in the Open Food Facts category taxonomy are also included (stored in `categories_full`)
- optionally specific locations (`locations`)

Its status is computed from `is_published` and the dates:

| Status | Rule |
|---|---|
| `DRAFT` | `is_published` is `False` |
| `UPCOMING` | published, `start_date` in the future |
| `ONGOING` | published, between `start_date` and `end_date` |
| `COMPLETED` | published, `end_date` in the past |

### Which prices & proofs are in a challenge?

A price is in a challenge if:

- it was **created** (not the price `date`!) between the challenge start & end dates
- and (if the challenge has categories) its `category_tag` is in the challenge `categories_full` (for `CATEGORY` prices), or its product `categories_tags` overlap the challenge `categories` (for `PRODUCT` prices)
- and (if the challenge has locations) its location is one of the challenge locations

A proof is in a challenge if at least one of its prices is.

### Challenge tags

Prices & proofs in a challenge are tagged with `challenge-<id>` (e.g. `challenge-12`) in their `tags` field. These tags are set automatically, they cannot be edited via the API:

- on price creation (async task): the price (and its proof) is tagged for each `ONGOING` challenge it matches
- daily (`update_challenge_task`): all matching prices & proofs are tagged, for challenges that are not completed or completed less than 7 days ago (after that, the challenge is "frozen")

Note: tags are only added, never removed (e.g. if a price is edited and no longer matches the challenge).

The tags can be used to filter the API, e.g. `/api/v1/prices?tags__contains=challenge-12`.

### Challenge stats

The challenge `stats` field is computed daily from the challenge tags: price, proof, user, product & location counts, as well as the top 10 users (by prices, proofs & prices from their proofs), locations and cities.

See `open_prices/challenges/models.py`

## Badges 🎖️

Badges reward contributors who reach a threshold on a given metric, e.g. "10 receipts uploaded". They are created by admins (in the Django admin).

see [https://prices.openfoodfacts.org/badges](https://prices.openfoodfacts.org/badges)

Every day (`update_badge_task`), users who have reached a badge threshold are given the badge. Badges are never taken away.

See `open_prices/badges/` & `/api/v1/badges`

## Rankings 🏅

We have a simple overall contributor ranking, as well as challenge-specific rankings (see [Challenge stats](#challenge-stats))

see [https://prices.openfoodfacts.org/stats](https://prices.openfoodfacts.org/stats)

## Future ideas 💡

- mayorship (top contributor of a location)
- yearly recap: a personal end-of-year summary of each contributor's activity (prices & proofs added, locations visited, challenges joined, badges earned...)

Have other ideas, or feedback on the existing ones? Anyone can join the conversation in the [Gamification discussion](https://github.com/openfoodfacts/open-prices/discussions/399) 🙌
