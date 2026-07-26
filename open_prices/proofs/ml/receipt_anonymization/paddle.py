"""Pydantic models to parse PaddleX /ocr results."""

from pydantic import BaseModel


class PaddleXDataInfo(BaseModel):
    width: int
    height: int
    type: str


class PaddleXPrunedResult(BaseModel):
    model_settings: dict
    dt_polys: list[list[list[float]]]
    text_det_params: dict
    text_type: str
    textline_orientation_angles: list[float]
    text_rec_score_thresh: float
    return_word_box: bool
    rec_texts: list[str]
    rec_scores: list[float]
    rec_polys: list[list[list[float]]]
    rec_boxes: list[list[float]]
    text_word: list[list[str]]
    text_word_boxes: list[list[list[float]]]
    doc_preprocessor_res: dict | None = None


class PaddleXOcrResultItem(BaseModel):
    prunedResult: PaddleXPrunedResult


class PaddleXOcrResult(BaseModel):
    ocrResults: list[PaddleXOcrResultItem]
    dataInfo: PaddleXDataInfo


class PaddleXOcrResponse(BaseModel):
    """A PaddleX OCR response, parsed from the JSON response body."""

    logId: str
    errorCode: int
    errorMsg: str
    result: PaddleXOcrResult
