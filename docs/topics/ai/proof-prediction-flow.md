# Proof & Price Tag Prediction Flow

This document maps prediction-related operations for both proof and price tag creation.

## Flow Diagram

```mermaid
graph TD
    A["Proof.save()"] -->|"post_save signal"| B["proof_post_save_run_ocr<br/><b>ASYNC TASK via django-q</b>"]
    A -->|"post_save signal"| C["proof_post_save_run_ml_models<br/><b>ASYNC TASK via django-q</b>"]

    B --> B1["fetch_and_save_ocr_data"]

    C --> D["run_and_save_proof_prediction"]
    D --> E["run_and_save_proof_type_prediction"]
    E --> E1["predict_proof_type<br/>Triton model"]
    E1 --> E2["ProofPrediction.create<br/>type=CLASSIFICATION"]

    D --> F{"proof.type == TYPE_PRICE_TAG?"}
    F -->|"Yes"| G["run_and_save_price_tag_detection"]
    G --> G1["detect_price_tags<br/>Triton model"]
    G1 --> G2["ProofPrediction.create<br/>type=OBJECT_DETECTION"]
    G2 --> G3["create_price_tags_from_proof_prediction"]
    G3 --> G4["FOR EACH detection (score >= threshold):<br/>PriceTag.create(created_by=None)"]
    G4 --> G5["run_and_save_price_tag_classification"]
    G5 --> G6["PriceTagPrediction.create<br/>type=PRICE_TAG_CLF"]
    G6 --> G7{"predicted type != invalid?"}
    G7 -->|"Yes"| H["run_and_save_price_tag_extraction"]
    H --> H1{PRICE_TAG_EXTRACTION_ASYNC_REQUESTS?}
    H1 -->|"Yes"| H2["Gemini API batch<br/><b>asyncio</b>"]
    H1 -->|"No"| H3["Gemini API sequential"]
    H2 --> H4["PriceTagPrediction.create<br/>type=PRICE_TAG_EXTRACTION"]
    H3 --> H4

    D --> I{"proof.type == TYPE_RECEIPT and run_receipt_extraction?"}
    I -->|"Yes"| J["run_and_save_receipt_extraction_prediction"]
    J --> J1["extract_from_receipt<br/>Gemini API"]
    J1 --> J2["ProofPrediction.create<br/>type=PROOF_PREDICTION_RECEIPT_EXTRACTION"]

    K["PriceTag.save() with created_by set"] -->|"post_save signal"| L["price_tag_post_save_run_ml_models<br/><b>ASYNC TASK via django-q</b>"]
    L --> L1["run_and_save_price_tag_classification_from_id"]
    L --> L2["run_and_save_price_tag_extraction_from_id"]
    L1 --> G5
    L2 --> H

    style A stroke:#2ecc71,stroke-width:3px
    style B stroke:#e74c3c,stroke-width:3px
    style B1 stroke:#2ecc71,stroke-width:3px
    style C stroke:#e74c3c,stroke-width:3px
    style D stroke:#2ecc71,stroke-width:3px
    style E stroke:#2ecc71,stroke-width:3px
    style E1 stroke:#2ecc71,stroke-width:3px
    style E2 stroke:#2ecc71,stroke-width:3px
    style G stroke:#2ecc71,stroke-width:3px
    style G1 stroke:#2ecc71,stroke-width:3px
    style G2 stroke:#2ecc71,stroke-width:3px
    style G3 stroke:#2ecc71,stroke-width:3px
    style G4 stroke:#2ecc71,stroke-width:3px
    style G5 stroke:#2ecc71,stroke-width:3px
    style G6 stroke:#2ecc71,stroke-width:3px
    style H stroke:#2ecc71,stroke-width:3px
    style H2 stroke:#e74c3c,stroke-width:3px
    style H3 stroke:#2ecc71,stroke-width:3px
    style H4 stroke:#2ecc71,stroke-width:3px
    style J stroke:#2ecc71,stroke-width:3px
    style J1 stroke:#2ecc71,stroke-width:3px
    style J2 stroke:#2ecc71,stroke-width:3px
    style K stroke:#2ecc71,stroke-width:3px
    style L stroke:#e74c3c,stroke-width:3px
    style L1 stroke:#2ecc71,stroke-width:3px
    style L2 stroke:#2ecc71,stroke-width:3px
```

## Notes

- Green border: synchronous execution.
- Red border: asynchronous execution (django-q task or asyncio batch).
- The proof-created flow and manual price-tag-created flow share the same price tag classification and extraction functions.

## Configuration

- `ENABLE_ML_PREDICTIONS`
- `ENABLE_OCR`
- `PRICE_TAG_EXTRACTION_ASYNC_REQUESTS`
