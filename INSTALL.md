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
Depending on your docker version you could either use `docker-compose` or `docker compose`.
Please adapt the script accordingly.
:::

create the dockers with

```sh
docker-compose up
```

The sever should be running on <http://localhost:8000/>.

The run the migration of the database with

```sh
make migrate-db
```

If you're using `docker compose`, this script might fail with the following error message:

```
make: docker-compose: No such file or directory
make: *** [Makefile:139: migrate-db] Error 127
```

To fix it, go in `Makefile` and replace `docker-compose` by `docker compose`.

Congrats, you can now contribute to the codebase :tada:

## Run locally

```
uvicorn app.api:app --reload
```

or use `--host` if you want to make it available on your local network, eg.:

```
uvicorn app.api:app --reload --host 192.168.0.100
```
