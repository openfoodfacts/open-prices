# Contributing to Open-Prices

## How to install on your local machine

see [INSTALL.md](https://github.com/openfoodfacts/open-prices/blob/main/INSTALL.md)

## Install pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com/) to enforce code styling, etc. To install it, run the following (in your virtual environment):

```
pre-commit install
```

Now `pre-commit` will run automatically on `git commit` :)

## Write and run tests

You should create unit tests for each new feature or API change (see [test_api.py](https://github.com/openfoodfacts/open-prices/blob/main/tests/test_api.py)).

To run tests, just launch:
```bash
pytest
```
