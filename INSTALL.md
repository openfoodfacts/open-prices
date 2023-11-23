# HOWTO install/test Open Prices API

## Prerequisites

- Python 3.10 (lower version may be OK, but untested)
- PostgreSQL 13 (lower version may be OK, but untested)

## Setup

### Without Docker

```
# clone repo
git clone https://github.com/openfoodfacts/open-prices.git
cd open-prices

# install poetry (Python dependency manager)
# see https://python-poetry.org/docs/

# install dependencies (pyproject.toml)
poetry install

# note: all future commands should be prefixed with `poetry run`

# run migrations
alembic upgrade head
```

### With Docker

TODO

## Run locally

```
uvicorn app.api:app --reload
```
or use `--host` if you want to make it available on your local network, eg.:
```
uvicorn app.api:app --reload --host 192.168.0.100
```
