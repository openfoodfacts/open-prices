# Contributing to Open Prices

## How to install on your local machine

see [INSTALL.md](https://github.com/openfoodfacts/open-prices/blob/main/INSTALL.md)

## Install pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com/) to enforce code styling, etc. To install it, run the following (in your virtual environment):

```
pre-commit install
```

Now `pre-commit` will run automatically on `git commit` :)

## Write and run tests

You should create basic tests for each new feature or API change.

To run tests locally, just launch:

```
poetry run python manage.py test
```
