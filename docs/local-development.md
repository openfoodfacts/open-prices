# Local development

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
