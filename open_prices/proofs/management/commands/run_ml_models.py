import argparse
import datetime

import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from openfoodfacts.utils import get_logger

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml import run_and_save_proof_prediction
from open_prices.proofs.ml.classification import PROOF_CLASSIFICATION_MODEL_NAME
from open_prices.proofs.ml.price_tags import (
    PRICE_TAG_DETECTOR_MODEL_NAME,
    run_and_save_price_tag_extraction,
)
from open_prices.proofs.models import PriceTagPrediction, Proof

# Initializing root logger
get_logger()


class Command(BaseCommand):
    help = """Run ML models on images with proof predictions, and save the predictions
    in DB."""
    _allowed_types = [
        "proof_classification",
        "price_tag_detection",
        "price_tag_extraction",
        "receipt_extraction",
    ]

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--limit", type=int, help="Limit the number of proofs to process."
        )
        parser.add_argument(
            "--types",
            type=str,
            help="Type of model to run. Supported values are `proof_classification`, "
            "`price_tag_detection` and `price_tag_extraction`. To pass multiple types, "
            "separate them with commas (e.g. `proof_classification,price_tag_detection`).",
        )
        parser.add_argument(
            "--delay",
            type=int,
            default=120,
            help="Only process proofs that were created before this delay (in seconds) from now.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write(
            "Running ML models on images without proof predictions for this model..."
        )
        limit = options["limit"]
        types_str = options["types"]
        delay = options["delay"]
        self.stdout.write(f"limit: {limit}, types: {types_str}, delay: {delay} seconds")

        if types_str:
            types = types_str.split(",")
        else:
            types = self._allowed_types

        if not all(t in self._allowed_types for t in types):
            raise ValueError(
                f"Invalid type(s) provided: '{types}', allowed: {self._allowed_types}"
            )

        if (
            "proof_classification" in types
            or "price_tag_detection" in types
            or "receipt_extraction" in types
        ):
            self.handle_proof_prediction_job(types, limit, delay)

        if "price_tag_extraction" in types:
            self.handle_price_tag_extraction_job(limit, delay)

    def handle_proof_prediction_job(
        self, types: list[str], limit: int, delay: int
    ) -> None:
        exclusion_filters_list = []
        if "proof_classification" in types:
            exclusion_filters_list.append(
                Q(predictions__model_name=PROOF_CLASSIFICATION_MODEL_NAME)
            )
        if "price_tag_detection" in types:
            exclusion_filters_list.append(
                Q(predictions__model_name=PRICE_TAG_DETECTOR_MODEL_NAME)
            )
        if "receipt_extraction" in types:
            exclusion_filters_list.append(
                Q(
                    predictions__type=proof_constants.PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE
                )
            )

        exclusion_filter = exclusion_filters_list.pop()
        for remaining_filter in exclusion_filters_list:
            exclusion_filter &= remaining_filter
        # Get proofs that don't have a proof prediction with
        # one of the model by performing an
        # outer join on the Proof and Prediction tables.
        proofs = (
            (
                Proof.objects.filter(
                    created__lt=timezone.now() - datetime.timedelta(seconds=delay),
                    predictions__model_name__isnull=True,
                )
                | Proof.objects.exclude(exclusion_filter)
            )
            .distinct()
            # Order by -id to process the most recent proofs first
            .order_by("-id")
        )

        if limit:
            proofs = proofs[:limit]

        for proof in tqdm.tqdm(proofs):
            self.stdout.write(f"Processing proof {proof.id}...")
            run_and_save_proof_prediction(
                proof,
                run_price_tag_extraction=False,
                run_receipt_extraction="receipt_extraction" in types,
            )
            self.stdout.write("Done.")

    def handle_price_tag_extraction_job(self, limit: int, delay: int) -> None:
        # Get all proofs of type PRICE_TAG
        proofs = Proof.objects.filter(
            created__lt=timezone.now() - datetime.timedelta(seconds=delay),
            type=proof_constants.TYPE_PRICE_TAG,
        ).order_by("-id")

        added = 0
        for proof in tqdm.tqdm(proofs):
            for price_tag in proof.price_tags.all():
                # Check if the price tag already has a prediction
                if not PriceTagPrediction.objects.filter(
                    type=proof_constants.PRICE_TAG_EXTRACTION_TYPE, price_tag=price_tag
                ).exists():
                    self.stdout.write(
                        f"Processing price tag {price_tag.id} (proof {proof.id})..."
                    )
                    run_and_save_price_tag_extraction([price_tag], proof)
                    added += 1
                    if limit and added >= limit:
                        return
