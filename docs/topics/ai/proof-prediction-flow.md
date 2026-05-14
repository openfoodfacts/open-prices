# Proof Prediction Flow

This document maps out the synchronous and asynchronous operations that occur when a proof is created, with a focus on the machine learning prediction pipeline.

## Overview

When a proof is saved, several prediction models are triggered:

- **Proof Type Classification** - Classifies the proof type (receipt, price tag, etc.)
- **Price Tag Detection** - Detects price tags in the image (for price tag proofs)
- **Price Tag Extraction** - Extracts barcode, price, and other data from each price tag (for price tag proofs)
- **Receipt Extraction** - Extracts items and prices from receipt images (for receipt proofs)

## Flow Diagram

```mermaid
graph TD
    A["📝 Proof.save()"] -->|"post_save signal"| G["proof_post_save_run_ocr<br/><b>ASYNC TASK via django-q</b>"]
    A -->|"post_save signal"| H["proof_post_save_run_ml_models<br/><b>ASYNC TASK via django-q</b>"]

    G --> G1["fetch_and_save_ocr_data"]

    H --> I["run_and_save_proof_prediction"]

    I --> J["run_and_save_proof_type_prediction"]
    J --> J1["predict_proof_type<br/>Triton model"]
    J1 --> J2["ProofPrediction.create<br/>type=CLASSIFICATION"]

    I --> K{"TYPE_PRICE_TAG?"}
    K -->|"Yes"| L["run_and_save_price_tag_detection"]
    L --> L1["detect_price_tags<br/>Triton model"]
    L1 --> L2["ProofPrediction.create<br/>type=OBJECT_DETECTION"]
    L1 --> L3["FOR EACH detection:"]
    L3 --> L3a["predict_price_tag_type<br/>Triton model"]
    L3a --> L3b["PriceTag.create"]
    L3b --> L3c["PriceTagPrediction.create<br/>type=CLASSIFICATION"]
    L3c --> L3d{"not invalid?"}
    L3d -->|"Yes"| L4["run_and_save_price_tag_extraction"]
    L4 --> L4b{ASYNC_REQUESTS?}
    L4b -->|"Yes"| L4c["Gemini API batch<br/><b>asyncio</b>"]
    L4b -->|"No"| L4d["Gemini API<br/>sequential"]
    L4c --> L4e["PriceTagPrediction.create<br/>type=EXTRACTION"]
    L4d --> L4e

    I --> M{"TYPE_RECEIPT?"}
    M -->|"Yes"| N["run_and_save_receipt_extraction_prediction"]
    N --> N1["extract_from_receipt<br/>Gemini API"]
    N1 --> N2["ProofPrediction.create<br/>type=RECEIPT_EXTRACTION"]
    N2 --> N3["FOR EACH item:<br/>ReceiptItem.create"]

    style A stroke:#2ecc71,stroke-width:3px
    style G stroke:#e74c3c,stroke-width:3px
    style G1 stroke:#2ecc71,stroke-width:3px
    style H stroke:#e74c3c,stroke-width:3px
    style I stroke:#2ecc71,stroke-width:3px
    style J stroke:#2ecc71,stroke-width:3px
    style J1 stroke:#2ecc71,stroke-width:3px
    style J2 stroke:#2ecc71,stroke-width:3px
    style L stroke:#2ecc71,stroke-width:3px
    style L1 stroke:#2ecc71,stroke-width:3px
    style L2 stroke:#2ecc71,stroke-width:3px
    style L3 stroke:#2ecc71,stroke-width:3px
    style L3a stroke:#2ecc71,stroke-width:3px
    style L3b stroke:#2ecc71,stroke-width:3px
    style L3c stroke:#2ecc71,stroke-width:3px
    style L4 stroke:#2ecc71,stroke-width:3px
    style L4c stroke:#e74c3c,stroke-width:3px
    style L4d stroke:#2ecc71,stroke-width:3px
    style L4e stroke:#2ecc71,stroke-width:3px
    style N stroke:#2ecc71,stroke-width:3px
    style N1 stroke:#2ecc71,stroke-width:3px
    style N2 stroke:#2ecc71,stroke-width:3px
    style N3 stroke:#2ecc71,stroke-width:3px
```

## Execution Model

### Synchronous (Green 🟢)
- User API call returns immediately after `Proof.save()` completes
- Database counts are updated synchronously
- Post-save signals execute in the same process

### Asynchronous (Pink 🔴)
- ML prediction pipeline runs in a **django-q worker process**
- OCR tasks run separately (if enabled)
- Nested asyncio for Gemini API batch requests (if `PRICE_TAG_EXTRACTION_ASYNC_REQUESTS=True`)

### Conditional (Yellow 🟡)
- Predictions vary based on `proof.type`
- Price tag extraction only runs on quality predictions (not "invalid")

## Key Implementation Details

### Proof Type Classification
- **Source**: `open_prices.proofs.ml.classification.run_and_save_proof_type_prediction()`
- **Model**: Triton (proof classification)
- **Stored as**: `ProofPrediction` with `type=CLASSIFICATION`

### Price Tag Detection (TYPE_PRICE_TAG only)
- **Source**: `open_prices.proofs.ml.price_tags.run_and_save_price_tag_detection()`
- **Model**: Triton (object detection)
- **Creates**: `ProofPrediction` + multiple `PriceTag` objects
- **Signal cascade**: Each `PriceTag.create` triggers image generation

### Price Tag Extraction (TYPE_PRICE_TAG only)
- **Source**: `open_prices.proofs.ml.price_tags.run_and_save_price_tag_extraction()`
- **Model**: Gemini (structured data extraction)
- **Creates**: `PriceTagPrediction` with barcode, price, and product info
- **Optimization**: Can batch Gemini requests with asyncio (controlled by `PRICE_TAG_EXTRACTION_ASYNC_REQUESTS`)

### Receipt Extraction (TYPE_RECEIPT only)
- **Source**: `open_prices.proofs.ml.receipts.run_and_save_receipt_extraction_prediction()`
- **Model**: Gemini (structured data extraction)
- **Creates**: `ProofPrediction` + multiple `ReceiptItem` objects
- **Lookup**: Matches extracted product names against existing prices for product codes

## Signal-Driven Count Updates

The following counts are updated via post-save signals:

| Model | Signal | Field Updated |
|-------|--------|---|
| `ProofPrediction` | `post_save` on create | `Proof.prediction_count += 1` |
| `PriceTagPrediction` | `post_save` on create | `PriceTag.prediction_count += 1` |
| `PriceTag` | `post_save` on create | triggers tag update and image generation |

## Configuration

Key settings that control this flow:

- `ENABLE_ML_PREDICTIONS` - Toggle entire ML pipeline
- `ENABLE_OCR` - Toggle OCR task
- `PRICE_TAG_EXTRACTION_ASYNC_REQUESTS` - Use asyncio batch for Gemini requests

## Files

- **Models**: `open_prices/proofs/models.py`
- **ML Pipeline**: `open_prices/proofs/ml/__init__.py`
- **Classification**: `open_prices/proofs/ml/classification.py`
- **Price Tags**: `open_prices/proofs/ml/price_tags.py`
- **Receipts**: `open_prices/proofs/ml/receipts.py`
- **OCR**: `open_prices/proofs/ml/ocr.py`
