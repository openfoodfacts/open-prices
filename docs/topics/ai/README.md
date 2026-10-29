# AI & Machine Learning

Documentation on the machine learning models and prediction pipelines used in Open Prices.

| Model | What it does | Runs on | Provider | Stored as | More info |
|---|---|---|---|---|---|
| OCR | extracts the text of the image | every proof | Google Cloud Vision | `.json.gz` file next to the image | unused |
| Proof classification | predicts the proof type (price tag, receipt...) | every proof | Triton (`price_proof_classification`) | `ProofPrediction` (`CLASSIFICATION`) | [Hugging Face](https://huggingface.co/openfoodfacts/price-proof-classification) |
| Price tag detection | detects price tags on the image, and creates a `PriceTag` for each one | `PRICE_TAG` proofs | Triton (`price_tag_detection`) | `ProofPrediction` (`OBJECT_DETECTION`) | [Hugging Face](https://huggingface.co/openfoodfacts/price-tag-detection) |
| Price tag classification | predicts the price tag quality (invalid, medium, high) | each price tag | Triton (`price_tag_classification`) | `PriceTagPrediction` (`PRICE_TAG_CLF`) | [Hugging Face](https://huggingface.co/openfoodfacts/price-tag-classification) |
| Price tag extraction | extracts the product, price, discount... | each price tag (not invalid) | Gemini | `PriceTagPrediction` (`PRICE_TAG_EXTRACTION`) | |
| Price tag extraction (WIP) | same as above, with a fine-tuned Qwen3 model (to replace Gemini) | | | | WIP, not integrated yet. [Hugging Face](https://huggingface.co/openfoodfacts/price-tag-extractor) |
| Receipt extraction | extracts the shop, date & items | `RECEIPT` proofs | Gemini | `ProofPrediction` (`RECEIPT_EXTRACTION`) | |
| Receipt anonymization | detects personal info (names, fidelity card ids) to hide with black boxes | `RECEIPT` proofs (draft only) | PaddleOCR + LLM (OpenAI-compatible API) | `ProofPrediction` (`RECEIPT_ANONYMIZATION`), deleted once the proof is no longer a draft | |

All models run asynchronously (Django Q tasks) when a proof is created (or when a price tag is added manually). On proof creation, they can be disabled with `ENABLE_ML_PREDICTIONS` (and OCR with `ENABLE_OCR`).

The code lives in `open_prices/proofs/ml/` (and [openfoodfacts-python](https://github.com/openfoodfacts/openfoodfacts-python))

## Providers

- **Triton**: [NVIDIA Triton Inference Server](https://github.com/triton-inference-server/server), self-hosted by Open Food Facts. It serves our own computer vision models (proof classification, price tag detection & classification). Configured with `TRITON_URI`
- **Gemini**: Google's LLM, called through its API to extract structured data (price tags & receipts). We plan to switch to an alternate LLM soon
- **Google Cloud Vision**: Google's OCR API
- **PaddleOCR**: OCR model, used with an LLM (through an OpenAI-compatible API) for receipt anonymization

## Pages

- **[Proof Prediction Flow](proof-prediction-flow.md)** - Map of sync/async operations when a proof is created, covering type classification, price tag detection, extraction, and receipt processing
