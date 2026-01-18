import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from openfoodfacts.taxonomy import Taxonomy, TaxonomyNode, get_taxonomy

from open_prices.common import openstreetmap

OFF_TAXONOMY_NAME = "country"
COUNTRY_CODES_TO_EXCLUDE = [
    "AQ",
    "GF",
    "GP",
    "MQ",
    "NC",
    "PF",
    "PM",
    "RE",
    "TF",
    "UK",
    "WF",
    "YT",
    "YU",
    "world",
]
OUTPUT_PATH = (
    settings.BASE_DIR / "open_prices" / "locations" / "data" / "countries.json"
)


def get_all_root_nodes(taxonomy: Taxonomy) -> list[TaxonomyNode]:
    return [node for node in taxonomy.iter_nodes() if not node.get_parents_hierarchy()]


def filter_node_list_by_rules(node_list: list[TaxonomyNode]) -> list[TaxonomyNode]:
    """
    Rules
    - keep only nodes with "country_code_2" property
    - remove some extra nodes
    """
    node_list_filtered_1 = [
        node for node in node_list if "country_code_2" in node.properties
    ]
    node_list_filtered_2 = [
        node
        for node in node_list_filtered_1
        if node.properties["country_code_2"]["en"] not in COUNTRY_CODES_TO_EXCLUDE
    ]
    return node_list_filtered_2


class Command(BaseCommand):
    """
    Usage:
    - python manage.py generate_countries_json
    - python manage.py generate_countries_json --enrich-with-osm-name
    """

    help = "Generate countries.json file from OpenFoodFacts taxonomy."

    def add_arguments(self, parser):
        parser.add_argument(
            "--enrich-with-osm-name",
            dest="enrich_with_osm_name",
            action="store_true",
            help="Enrich countries with OpenStreetMap country name.",
            default=False,
        )

    def handle(self, *args, **options):
        self.stdout.write("Generating countries.json file...")

        # Step 1: get the full taxonomy
        countries_all: Taxonomy = get_taxonomy(
            OFF_TAXONOMY_NAME, force_download=True, download_newer=True
        )
        self.stdout.write(f"Taxonomy: number of nodes: {len(countries_all)}")

        # Step 2: filter nodes according to rules (keep only root nodes with country_code_2)
        countries_filtered = get_all_root_nodes(countries_all)
        countries_filtered = filter_node_list_by_rules(countries_filtered)
        self.stdout.write(
            f"Number of countries (after filtering): {len(countries_filtered)}"
        )

        # Step 3a: build countries list
        countries = []
        for node in countries_filtered:
            country_code = node.properties["country_code_2"]["en"]
            country_dict = {
                "id": node.id,
                "name": node.get_localized_name("en"),
                "country_code_2": country_code,
                # "osm_name": see below
            }
            countries.append(country_dict)

        # Step 3b: sort countries by country_code_2
        countries = sorted(countries, key=lambda x: x["country_code_2"])

        # Step 3c: enrich with OSM names if needed
        if options["enrich_with_osm_name"]:
            self.stdout.write("Enriching countries with OSM names...")
            # Step 3c1: fetch OSM countries data from Overpass API
            response = requests.post(
                openstreetmap.OVERPASS_API_URL,
                data={"data": openstreetmap.COUNTRIES_OVERPASS_QUERY},
            )
            osm_countries_data = response.json()
            self.stdout.write(
                f"OSM countries fetched: {len(osm_countries_data['elements'])}"
            )
            # Step 3c2: enrich countries with OSM names
            for i, country in enumerate(countries):
                country_code = country["country_code_2"]
                for osm_country in osm_countries_data["elements"]:
                    if "tags" in osm_country and "ISO3166-1" in osm_country["tags"]:
                        if osm_country["tags"]["ISO3166-1"] == country_code:
                            countries[i]["osm_name"] = osm_country["tags"].get("name")
            self.stdout.write(
                f"Countries with OSM name: {len([c for c in countries if 'osm_name' in c])}"
            )
            self.stdout.write(
                f"Countries without OSM name: {[c['name'] for c in countries if 'osm_name' not in c]}"
            )

        # Step 4: write countries to file
        with open(OUTPUT_PATH, "w") as f:
            json.dump(countries, f, ensure_ascii=False)  # indent=4
        self.stdout.write(f"Done! Wrote to {OUTPUT_PATH}")
