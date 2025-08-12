# Maintenance

## How to launch OCR on previously uploaded images

OCR (through Google Cloud Vision) is launched on every new proof image. However, if you want to launch OCR on previously uploaded images, you can do so by running the following command:

```bash
make cli args='run_ocr'
```

To override existing OCR results, add the `--override` flag:

```bash
make cli args='run_ocr --override'
```

## How to run ML models

Sometimes, due to Triton or Gemini API being unavailable (or any other issue), ML models may fail to run. If you want to retry running the ML models, you can do so by running the following command:

```bash
make cli args='run_ml_models'
```

This run the following models:

- `proof_classification` (detect the proof type)
- `price_tag_detection` (the object detection model that detects the spacial position of each price tag, only if the proof is a price tag)
- `receipt_extraction` (Gemini extraction for receipt, if the proof is a receipt)
- `price_tag_extraction` (Gemini extraction of price tags, if the proof is a price tag)

If you want to run only a specific model, you can do so by passing the model name with `--types` flag. You can pass multiple model names separated by commas. For example, to run only the `proof_classification` and `price_tag_detection` models, you can run:

```bash
make cli args='run_ml_models --types proof_classification,price_tag_detection'
```
