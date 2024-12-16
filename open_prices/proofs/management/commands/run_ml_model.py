import argparse

import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q
from openfoodfacts.utils import get_logger

from open_prices.proofs.ml import (
    PRICE_TAG_DETECTOR_MODEL_NAME,
    PROOF_CLASSIFICATION_MODEL_NAME,
    run_and_save_proof_prediction,
)
from open_prices.proofs.models.proof import Proof

# Initializing root logger
get_logger()


class Command(BaseCommand):
    help = """Run ML models on images with proof predictions, and save the predictions
    in DB."""
    _allowed_types = ["proof_classification", "price_tag_detection"]

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--limit", type=int, help="Limit the number of proofs to process."
        )
        parser.add_argument(
            "--types",
            type=str,
            help="Type of model to run. Supported values are `proof_classification` "
            "and `price_tag_detection`",
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write(
            "Running ML models on images without proof predictions for this model..."
        )
        limit = options["limit"]
        types_str = options["types"]

        if types_str:
            types = types_str.split(",")
        else:
            types = self._allowed_types

        if not all(t in self._allowed_types for t in types):
            raise ValueError(
                f"Invalid type(s) provided: '{types}', allowed: {self._allowed_types}"
            )

        exclusion_filters_list = []
        if "proof_classification" in types:
            exclusion_filters_list.append(
                Q(predictions__model_name=PROOF_CLASSIFICATION_MODEL_NAME)
            )

        if "price_tag_detection" in types:
            exclusion_filters_list.append(
                Q(predictions__model_name=PRICE_TAG_DETECTOR_MODEL_NAME)
            )

        exclusion_filter = exclusion_filters_list.pop()
        for remaining_filter in exclusion_filters_list:
            exclusion_filter &= remaining_filter
        # Get proofs that don't have a proof prediction with
        # one of the model by performing an
        # outer join on the Proof and Prediction tables.
        proofs = (
            Proof.objects.filter(predictions__model_name__isnull=True)
            | Proof.objects.exclude(exclusion_filter)
        ).distinct()

        if limit:
            proofs = proofs[:limit]

        for proof in tqdm.tqdm(proofs):
            self.stdout.write(f"Processing proof {proof.id}...")
            run_and_save_proof_prediction(proof.id)
            self.stdout.write("Done.")
