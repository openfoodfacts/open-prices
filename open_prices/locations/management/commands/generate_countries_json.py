import json

from django.conf import settings
from django.core.management.base import BaseCommand
from openfoodfacts.taxonomy import Taxonomy, TaxonomyNode, get_taxonomy

TAXONOMY_NAME = "country"
OUTPUT_PATH = (
    settings.BASE_DIR / "open_prices" / "locations" / "data" / "countries.json"
)


def get_all_root_nodes(taxonomy: Taxonomy) -> list[TaxonomyNode]:
    return [node for node in taxonomy.iter_nodes() if not node.get_parents_hierarchy()]


def filter_node_list_by_rules(node_list: list[TaxonomyNode]) -> list[TaxonomyNode]:
    """
    Rules
    - keep only nodes with "country_code_2" property
    """
    return [node for node in node_list if "country_code_2" in node.properties]


class Command(BaseCommand):
    """
    Usage: python manage.py generate_countries_json
    """

    help = "Generate countries.json file from OpenFoodFacts taxonomy."

    def handle(self, *args, **options):
        self.stdout.write("Generating countries.json file...")

        # Step 1: get the full taxonomy
        TAXONOMY_FULL: Taxonomy = get_taxonomy(
            TAXONOMY_NAME, force_download=True, download_newer=True
        )
        self.stdout.write(f"Taxonomy: total number of nodes: {len(TAXONOMY_FULL)}")

        # Step 2: filter nodes according to rules (keep only root nodes with country_code_2)
        countries_filtered = get_all_root_nodes(TAXONOMY_FULL)
        countries_filtered = filter_node_list_by_rules(countries_filtered)
        self.stdout.write(
            f"Total number of countries: {len(countries_filtered)} with country_code_2"
        )

        # Step 3a: build countries list
        countries = []
        for node in countries_filtered:
            country_code = node.properties["country_code_2"]["en"]
            country_node = {
                "id": node.id,
                "name": node.get_localized_name("en"),
                "country_code_2": country_code,
                # "osm_name": get_country_osm_name(OPENSTREETMAP_COUNTRIES, country_code),
            }
            countries.append(country_node)

        # Step 3b: sort countries by country_code_2
        countries = sorted(countries, key=lambda x: x["country_code_2"])

        # Step 4: write countries to file
        with open(OUTPUT_PATH, "w") as f:
            json.dump(countries, f, ensure_ascii=False)  # indent=4
        print(f"Done! Wrote to {OUTPUT_PATH}")
