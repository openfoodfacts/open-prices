# Maintenance

## SDK Update Notifications

The Open Prices project includes an automated system to notify SDK maintainers when API changes are released.

### How it works

The **SDK Update Notification** workflow (`.github/workflows/sdk-update-notification.yml`) automatically triggers when:

1. A new release is published
2. The release title or body contains the word "API"

The workflow then:

- Scans the release notes for API-related changes
- Creates standardized issues in all OpenFoodFacts SDK repositories
- Includes links to the release notes and API documentation
- Prevents duplicate notifications by checking for existing issues

### Target SDK repositories

The following repositories will receive automatic notifications:

- `openfoodfacts/openfoodfacts-php`
- `openfoodfacts/openfoodfacts-js`
- `openfoodfacts/openfoodfacts-laravel`
- `openfoodfacts/openfoodfacts-python`
- `openfoodfacts/openfoodfacts-ruby`
- `openfoodfacts/openfoodfacts-java`
- `openfoodfacts/openfoodfacts-elixir`
- `openfoodfacts/openfoodfacts-dart`
- `openfoodfacts/openfoodfacts-go`

### Issue format

Created issues include:

- **Title**: "Update SDK for Open Prices API changes (vX.X.X)"
- **Labels**: `api-update`, `enhancement`
- **Content**: 
  - Summary of API changes detected
  - Link to release notes
  - Links to API documentation
  - Action items for SDK maintainers

### Monitoring

The workflow provides detailed logging and will:

- Skip repositories that are not accessible
- Log successful issue creation with URLs
- Report any errors encountered during execution

### Manual override

If you need to manually notify SDK repositories about API changes, you can re-run the workflow by creating a new release or tag that mentions "API" in the title or description.

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
