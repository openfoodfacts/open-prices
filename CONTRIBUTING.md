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

## Generate the SQL schema image

```
poetry run python manage.py graph_models -a -X ContentType,LogEntry,AbstractUser,AbstractBaseSession,Group,Permission,Success,Failure,Task,Schedule,OrmQ,User,Session -o docs/schema/2024-09-22_price-schema.png
```
