# HOWTO install/test Open Prices API

## Prerequisites

- Python 3.11 (lower version may be OK, but untested)
- PostgreSQL 13 (lower version may be OK, but untested)

## Setup

### Without Docker

```
# clone repo
git clone https://github.com/openfoodfacts/open-prices.git
cd open-prices

# install poetry (Python dependency manager) at version 1.6.1
# see https://python-poetry.org/docs/

# install dependencies (pyproject.toml)
poetry install

# note: all future commands should be prefixed with `poetry run`

# run migrations
alembic upgrade head
```

### With Docker

:::info
Open Prices now only supports docker compose v2 (`docker compose`)
:::

create the dockers with

```sh
docker compose up
```

The sever should be running on <http://localhost:8000/>.

The run the migration of the database with

```sh
make migrate-db
```

The load the fixtures with

```sh
make load-fixtures
```

Congrats, you can now contribute to the codebase :tada:

## Run locally

```
uvicorn app.api:app --reload
```

or use `--host` if you want to make it available on your local network, eg.:

```
uvicorn app.api:app --reload --host 192.168.0.100
```
