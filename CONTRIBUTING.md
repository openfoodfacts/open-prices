# Contributing to Open Prices

## How to install on your local machine

see [INSTALL.md](INSTALL.md)

## Install pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com/) to enforce code styling, etc. To install it, run the following:

```
uv run pre-commit install
```

Now `pre-commit` will run automatically on `git commit` :)

## Write and run tests

You should create basic tests for each new feature or API change.

To run tests locally, just launch:

```
uv run --env-file .env python manage.py test
```

## Preview the docs locally

```bash
uv run mkdocs serve -a 127.0.0.1:8765
```

Open http://127.0.0.1:8765/ in your browser.

## Generate the SQL schema image

```
uv run --env-file .env python manage.py graph_models -a -X ContentType,LogEntry,AbstractUser,AbstractBaseSession,Group,Permission,Success,Failure,Task,Schedule,OrmQ,User,Session -o docs/schema/schema.png
```

## Work with ML models

When uploading a proof, machine learning models are run asynchronously in the background, thanks to Django Q2.

However, it still requires a Triton server to be running, as well as a Gemini API key to be set in the environment variables.

Triton is used to:

- detect the proof type (`proof_classification`)
- detect price tags on the proof (`price_tag_detection`)

Gemini is used to:

- extract information from receipts (`receipt_extraction`)
- extract information from price tags (`price_tag_extraction`)

To run Triton, you should first clone the Robotoff repository.

Then, download the object detection models:
```bash
make dl-object-detection-models
```

Then, run the Triton server:

```bash
make up service=triton
```

You can check with `docker logs triton` that the server is running correctly.

For Gemini, the easiest way to set it up is to use the Gemini API. You can set your API key by overriding the `GEMINI_API_KEY` environment variable in your `.envrc` file:

```bash
export GEMINI_API_KEY=your_api_key_here
```

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
