import logging

import cv2
import numpy as np
from django.conf import settings
from openfoodfacts.ml.image_classification import ImageClassifier
from pydantic import BaseModel, Field

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import Proof, ProofPrediction

logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    """Configuration of an image classification model."""

    model_name: str = Field(
        ...,
        description="The name of the model, it will be used when saving the prediction in DB.",
    )
    model_version: str = Field(
        ...,
        description="The version of the model, it will be used when saving the prediction in DB.",
    )
    triton_version: str = Field(
        ...,
        description="The version of the model used on Triton Inference Server (eg: `1`)",
    )
    triton_model_name: str = Field(
        ..., description="The name of the model on Triton Inference Server"
    )
    image_size: int = Field(
        ...,
        description="The size of the image expected by the model. "
        "The original image will be resized to this size.",
    )
    label_names: list[str] = Field(
        ...,
        description="The names of the labels used by the model. "
        "The order of the labels must match the order of the classes in the model.",
    )


proof_classification_model_config = ModelConfig(
    model_name="price_proof_classification",
    model_version="price_proof_classification-1.0",
    triton_version="1",
    triton_model_name="price_proof_classification",
    image_size=224,
    label_names=[
        "OTHER",
        "PRICE_TAG",
        "PRODUCT_WITH_PRICE",
        "RECEIPT",
        "SHELF",
        "WEB_PRINT",
    ],
)

price_tag_classification_model_config = ModelConfig(
    model_name="price_tag_classification",
    model_version="price_tag_classification-1.0",
    triton_version="1",
    triton_model_name="price_tag_classification",
    image_size=960,
    label_names=["invalid", "medium-quality", "high-quality"],
)


def classify(
    image: np.ndarray, model_config: ModelConfig, triton_uri: str = settings.TRITON_URI
) -> list[tuple[str, float]]:
    """Run inference for an image classification model, and return the results as a
    list of tuples (label, confidence).

    :param image: the input image, as a numpy array (uint8, in BGR format)
    :param model_config: the configuration of the model to use for classification
    :param triton_uri: the URI of the Triton server, defaults to settings.TRITON_URI
    :return: the prediction results as a list of tuples (label, confidence)
    """
    classifier = ImageClassifier(
        model_name=model_config.model_name,
        label_names=model_config.label_names,
        image_size=model_config.image_size,
    )
    # Convert image from BGR to RGB format, as expected by the model
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = classifier.predict(
        image,
        triton_uri=triton_uri,
        model_version=model_config.triton_version,
    )
    return results.predictions


def predict_proof_type(
    image: np.ndarray, triton_uri: str = settings.TRITON_URI
) -> list[tuple[str, float]]:
    """Predict the type of a proof image.

    :param image: the input image, as a numpy array (uint8, in BGR format)
    :param triton_uri: the URI of the Triton server, defaults to settings.TRITON_URI
    :return: the prediction results as a list of tuples (label, confidence)
    """
    return classify(
        image=image,
        model_config=proof_classification_model_config,
        triton_uri=triton_uri,
    )


def predict_price_tag_type(
    image: np.ndarray,
    triton_uri: str = settings.TRITON_URI,
) -> list[tuple[str, float]]:
    """Predict the type of a price tag image.

    :param image: the input image, as a numpy array (uint8, in BGR format)
    :param triton_uri: the URI of the Triton server, defaults to settings.TRITON_URI
    :return: the prediction results as a list of tuples (label, confidence)
    """
    return classify(
        image=image,
        model_config=price_tag_classification_model_config,
        triton_uri=triton_uri,
    )


def run_and_save_proof_type_prediction(
    image: np.ndarray, proof: Proof, overwrite: bool = False
) -> ProofPrediction | None:
    """Run the proof type classifier model and save the prediction in
    ProofPrediction table.

    :param image: the image to run the model on, as a numpy array (uint8, in BGR
        format)
    :param proof: the Proof instance to associate the ProofPrediction with
    :param overwrite: whether to overwrite existing prediction, defaults to
        False
    :return: the ProofPrediction instance created, or None if the prediction
        already exists and overwrite is False
    """
    if ProofPrediction.objects.filter(
        proof=proof, model_name=proof_classification_model_config.model_name
    ).exists():
        if overwrite:
            logger.info("Overwriting existing type prediction for proof %s", proof.id)
            ProofPrediction.objects.filter(
                proof=proof, model_name=proof_classification_model_config.model_name
            ).delete()
        else:
            logger.debug(
                "Proof %s already has a prediction for model %s",
                proof.id,
                proof_classification_model_config.model_name,
            )
            return None

    prediction = predict_proof_type(image)

    max_confidence = max(prediction, key=lambda x: x[1])[1]
    proof_type = max(prediction, key=lambda x: x[1])[0]
    try:
        return ProofPrediction.objects.create(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
            model_name=proof_classification_model_config.model_name,
            model_version=proof_classification_model_config.model_version,
            data={
                "prediction": [
                    {"label": label, "score": confidence}
                    for label, confidence in prediction
                ]
            },
            value=proof_type,
            max_confidence=max_confidence,
        )
    except Exception as e:
        logger.exception(e)
        return None
