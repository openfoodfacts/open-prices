import functools
import logging
import math
import time
import typing
from pathlib import Path

import grpc
import numpy as np
from django.conf import settings
from PIL import Image, ImageOps
from tritonclient.grpc import service_pb2, service_pb2_grpc
from tritonclient.grpc.service_pb2_grpc import GRPCInferenceServiceStub

from .. import constants
from ..models import Proof, ProofPrediction

logger = logging.getLogger(__name__)


PROOF_CLASSIFICATION_LABEL_NAMES = [
    "OTHER",
    "PRICE_TAG",
    "PRODUCT_WITH_PRICE",
    "RECEIPT",
    "SHELF",
    "WEB_PRINT",
]
PROOF_CLASSIFICATION_MODEL_NAME = "price_proof_classification"
PROOF_CLASSIFICATION_MODEL_VERSION = "price_proof_classification-1.0"


@functools.cache
def get_triton_inference_stub(
    triton_uri: str | None = None,
) -> GRPCInferenceServiceStub:
    """Return a gRPC stub for Triton Inference Server.

    If `triton_uri` is not provided, the default value from settings is used.

    :param triton_uri: URI of the Triton Inference Server, defaults to None
    :return: gRPC stub for Triton Inference Server
    """
    triton_uri = triton_uri or settings.TRITON_URI
    channel = grpc.insecure_channel(triton_uri)
    return service_pb2_grpc.GRPCInferenceServiceStub(channel)


def classify_transforms(
    img: Image.Image,
    size: int = 224,
    mean: tuple[float, float, float] = (0.0, 0.0, 0.0),
    std: tuple[float, float, float] = (1.0, 1.0, 1.0),
    interpolation: Image.Resampling = Image.Resampling.BILINEAR,
    crop_fraction: float = 1.0,
) -> np.ndarray:
    """
    Applies a series of image transformations including resizing, center
    cropping, normalization, and conversion to a NumPy array.

    Transformation steps is based on the one used in the Ultralytics library:
    https://github.com/ultralytics/ultralytics/blob/main/ultralytics/data/augment.py#L2319

    :param img: Input Pillow image.
    :param size: The target size for the transformed image (shortest edge).
    :param mean: Mean values for each RGB channel used in normalization.
    :param std: Standard deviation values for each RGB channel used in
        normalization.
    :param interpolation: Interpolation method from PIL (
    Image.Resampling.NEAREST, Image.Resampling.BILINEAR,
    Image.Resampling.BICUBIC).
    :param crop_fraction: Fraction of the image to be cropped.
    :return: The transformed image as a NumPy array.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Rotate the image based on the EXIF orientation if needed
    img = typing.cast(Image.Image, ImageOps.exif_transpose(img))

    # Step 1: Resize while preserving the aspect ratio
    width, height = img.size

    # Calculate scale size while preserving aspect ratio
    scale_size = math.floor(size / crop_fraction)

    aspect_ratio = width / height
    if width < height:
        new_width = scale_size
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = scale_size
        new_width = int(new_height * aspect_ratio)

    img = img.resize((new_width, new_height), interpolation)

    # Step 2: Center crop
    left = (new_width - size) // 2
    top = (new_height - size) // 2
    right = left + size
    bottom = top + size
    img = img.crop((left, top, right, bottom))

    # Step 3: Convert the image to a NumPy array and scale pixel values to
    # [0, 1]
    img_array = np.array(img).astype(np.float32) / 255.0

    # Step 4: Normalize the image
    mean_np = np.array(mean, dtype=np.float32).reshape(1, 1, 3)
    std_np = np.array(std, dtype=np.float32).reshape(1, 1, 3)
    img_array = (img_array - mean_np) / std_np

    # Step 5: Change the order of dimensions from (H, W, C) to (C, H, W)
    img_array = np.transpose(img_array, (2, 0, 1))
    return img_array


class ImageClassifier:
    def __init__(self, model_name: str, label_names: list[str]):
        self.model_name: str = model_name
        self.label_names = label_names

    def predict(
        self,
        image: Image.Image,
        triton_uri: str | None = None,
    ) -> list[tuple[str, float]]:
        """Run an image classification model on an image.

        The model is expected to have been trained with Ultralytics library
        (Yolov8).

        :param image: the input Pillow image
        :param triton_uri: URI of the Triton Inference Server, defaults to
            None. If not provided, the default value from settings is used.
        :return: the prediction results as a list of tuples (label, confidence)
        """
        image_array = classify_transforms(image)
        image_array = np.expand_dims(image_array, axis=0)

        grpc_stub = get_triton_inference_stub(triton_uri)
        request = service_pb2.ModelInferRequest()
        request.model_name = self.model_name

        image_input = service_pb2.ModelInferRequest().InferInputTensor()
        image_input.name = "images"

        image_input.datatype = "FP32"

        image_input.shape.extend([1, 3, 224, 224])
        request.inputs.extend([image_input])

        output = service_pb2.ModelInferRequest().InferRequestedOutputTensor()
        output.name = "output0"
        request.outputs.extend([output])

        request.raw_input_contents.extend([image_array.tobytes()])
        start_time = time.monotonic()
        response = grpc_stub.ModelInfer(request)
        latency = time.monotonic() - start_time

        logger.debug("Inference time for %s: %s", self.model_name, latency)

        start_time = time.monotonic()
        if len(response.outputs) != 1:
            raise Exception(f"expected 1 output, got {len(response.outputs)}")

        if len(response.raw_output_contents) != 1:
            raise Exception(
                f"expected 1 raw output content, got {len(response.raw_output_contents)}"
            )

        output_index = {output.name: i for i, output in enumerate(response.outputs)}
        output = np.frombuffer(
            response.raw_output_contents[output_index["output0"]],
            dtype=np.float32,
        ).reshape((1, len(self.label_names)))[0]

        score_indices = np.argsort(-output)

        latency = time.monotonic() - start_time
        logger.debug("Post-processing time for %s: %s", self.model_name, latency)
        return [(self.label_names[i], float(output[i])) for i in score_indices]


def predict_proof_type(image: Image.Image) -> list[tuple[str, float]]:
    """Predict the type of a proof image.

    :param image: the input Pillow image
    :return: the prediction results as a list of tuples (label, confidence)
    """
    classifier = ImageClassifier(
        PROOF_CLASSIFICATION_MODEL_NAME, PROOF_CLASSIFICATION_LABEL_NAMES
    )
    return classifier.predict(image)


def run_and_save_proof_prediction(proof_id: int) -> None:
    """Run the proof classification model on a proof image and save the
    results in DB.

    :param proof_id: the ID of the proof to be classified
    """
    proof = Proof.objects.filter(id=proof_id).first()
    if not proof:
        logger.error("Proof with id %s not found", proof_id)
        return

    file_path_full = proof.file_path_full

    if file_path_full is None or not Path(file_path_full).exists():
        logger.error("Proof file not found: %s", file_path_full)
        return

    image = Image.open(file_path_full)
    prediction = predict_proof_type(image)

    max_confidence = max(prediction, key=lambda x: x[1])[1]
    proof_type = max(prediction, key=lambda x: x[1])[0]
    ProofPrediction.objects.create(
        proof=proof,
        type=constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
        model_name=PROOF_CLASSIFICATION_MODEL_NAME,
        model_version=PROOF_CLASSIFICATION_MODEL_VERSION,
        data={
            "prediction": [
                {"label": label, "score": confidence}
                for label, confidence in prediction
            ]
        },
        value=proof_type,
        max_confidence=max_confidence,
    )
