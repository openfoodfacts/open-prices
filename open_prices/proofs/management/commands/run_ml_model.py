import argparse

import tqdm
from django.core.management.base import BaseCommand

from open_prices.proofs.ml.image_classifier import (
    PROOF_CLASSIFICATION_MODEL_NAME,
    run_and_save_proof_prediction,
)
from open_prices.proofs.models import Proof


class Command(BaseCommand):
    help = """Run ML models on images with proof predictions, and save the predictions
    in DB."""
    _allowed_types = ["proof_classification"]

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--limit", type=int, help="Limit the number of proofs to process."
        )
        parser.add_argument("type", type=str, help="Type of model to run.", nargs="+")

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write(
            "Running ML models on images without proof predictions for this model..."
        )
        limit = options["limit"]
        types = options["type"]

        if not all(t in self._allowed_types for t in types):
            raise ValueError(
                f"Invalid type(s) provided: {types}, allowed: {self._allowed_types}"
            )

        if "proof_classification" in types:
            # Get proofs that don't have a proof prediction with
            # model_name = PROOF_CLASSIFICATION_MODEL_NAME by performing an
            # outer join on the Proof and Prediction tables.
            proofs = (
                Proof.objects.filter(predictions__model_name__isnull=True)
                | Proof.objects.exclude(
                    predictions__model_name=PROOF_CLASSIFICATION_MODEL_NAME
                )
            ).distinct()

            if limit:
                proofs = proofs[:limit]

            for proof in tqdm.tqdm(proofs):
                self.stdout.write(f"Processing proof {proof.id}...")
                run_and_save_proof_prediction(proof.id)
                self.stdout.write("Done.")
