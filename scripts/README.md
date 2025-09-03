# Scripts

This directory contains scripts related to the Open Prices project.

## `anonymize_receipts.py`

This script is used to anonymize receipt images by redacting personal information such as last names (client or cashier), fidelity card numbers and the hour of the purchase. It utilizes Gemini model to detect personal information, then uses OCR (with Google Cloud Vision) to locate the information in the image. We then redact the identified information from the image and save the anonymized version.

### Installation

Using uv is the recommended way to run the script. First,  [install uv](https://docs.astral.sh/uv/getting-started/installation/).

Then, simply run:

```bash
uv run scripts.anonymize_receipts --help
```

This will install the required dependencies in an isolated environment and display the help message.

This script can use either Gemini via Vertex AI or via the Gemini API. For stronger privacy, it is recommended to use Vertex AI.

To use Vertex AI, the following environment variables must be set:

- `GOOGLE_GENAI_USE_VERTEXAI`: Set to `1` to force the use of Vertex AI for Gemini access.
- `GOOGLE_CLOUD_LOCATION`: The Google Cloud location to use (recommended in Europe: `europe-west1`).

You must also have a Google service account key (JSON file) in `$HOME/.config/gcloud/application_default_credentials.json`.

To user the Gemini API, set the following environment variable:
- `GEMINI_API_KEY`: Your Gemini API key.

For the OCR, the script uses the Google Cloud Vision API. You must set the following environment variable:
- `GOOGLE_API_KEY`: Your Google Cloud API key with access to the Google Cloud Vision API.

### Usage

The script accepts two positional arguments: `input_dir` and `output_dir`, which are the paths to the input and output directories respectively. All receipt images must be in the input directory. The script will process each image, anonymize it, and save the result in the output directory, in one of the following subdirectory:

- `redacted`: all personal information detected by Gemini were located in the image and redacted.
- `kept`: no personal information were detected by Gemini, the image was copied as is.
- `partial`: some personal information detected by Gemini were located in the image and redacted, but some were not found (e.g. the fidelity card number was detected but not found in OCR results).

The name of the output file will be the same as the input file.

For example, to anonymize all receipt images in the `data/receipts` directory and save the results in the `data/anonymized_receipts` directory, run:

```bash
uv run anonymize_receipts.py data/receipts data/anonymized_receipts
```

To keep track of Gemini prediction, add the `--save-prediction` flag. This will save a JSON file with the same name as the image at the same location as the output image.

### Troubleshooting

By default, if an error occurs during the processing of an image, the error will be printed to stderr, and the script will continue processing the next image. You can disable this behavior by providing the `--no-skip-error` flag. In this case, the script will stop at the first error.

In any case, you can relaunch the script on the same input and output directories. The script will skip already processed images.

The following error may occur: `UnidentifiedImageError: cannot identify image file`.

It probably means that the image file is corrupted or that the extension is incorrect. Use the `identify` command to check:

```bash
identify path/to/image
```
