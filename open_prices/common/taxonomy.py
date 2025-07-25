import functools

from openfoodfacts.taxonomy import (
    create_taxonomy_mapping,
    get_taxonomy,
    map_to_canonical_id,
)
from openfoodfacts.utils.text import get_tag

# Taxonomy mapping generation takes ~200ms, so we cache it to avoid
# recomputing it for each request.
create_taxonomy_mapping_cached = functools.lru_cache()(create_taxonomy_mapping)
# Also cache the get_taxonomy function to avoid reading from disk at each
# request.
get_taxonomy_cached = functools.lru_cache()(get_taxonomy)


def normalize_taxonomized_tags(
    taxonomy_type: str, value_tags: list[str], force_match: bool = False
) -> list[str] | list[str | None]:
    """Normalizes a list of tags based on the taxonomy type.

    :param taxonomy_type: The type of taxonomy ('category', 'label', or
        'origin').
    :param value_tags: A list of tag values to normalize (e.g.,
        ["fr: Boissons"]).
    :param force_match: If True, will force the mapping of tags to their
        canonical ID. If the tag does not exist in the taxonomy, we return
        None instead of the tag version of the value. If False, the tag
        version of the value will be returned even when it does not exist in
        the taxonomy.
    :raises RuntimeError: If the taxonomy type is not one of 'category',
        'label', or 'origin'
    :raises ValueError: If the value_tag could not be mapped to a canonical ID.
    :return: The normalized tags (e.g., ["en:beverages"]). The order of the
        tags is the same as the input list.
    """
    if taxonomy_type not in ("category", "label", "origin"):
        raise RuntimeError(
            f"Invalid taxonomy type: {taxonomy_type}. Expected one of 'category', 'label', or 'origin'."
        )

    # Use the cached version of the get_taxonomy function to avoid
    # creating it multiple times.
    taxonomy = get_taxonomy_cached(taxonomy_type)
    # the tag (category or label tag) can be provided by the mobile app in any
    # language, with language prefix (ex: `fr: Boissons`).
    # We need to map it to the canonical id (ex: `en:beverages`) to store it
    # in the database.
    # The `map_to_canonical_id` function maps the value (ex:
    # `fr: Boissons`) to the canonical id (ex: `en:beverages`).
    # We use the cached version of this function to avoid
    # creating it multiple times.
    # If the entry does not exist in the taxonomy, the tag will
    # be set to the tag version of the value (ex: `fr:boissons`).
    taxonomy_mapping = create_taxonomy_mapping_cached(taxonomy)
    unnormalized_tags = [get_tag(tag) for tag in value_tags]
    mapped_tags = map_to_canonical_id(taxonomy_mapping, value_tags)
    # Keep the order of the tags as they were provided

    normalized_tags: list[str] | list[str | None] = [
        mapped_tags[k] for k in mapped_tags
    ]
    if force_match:
        for i in range(len(normalized_tags)):
            if (
                normalized_tags[i] == unnormalized_tags[i]
                and normalized_tags[i] not in taxonomy
            ):
                normalized_tags[i] = None

    return normalized_tags
