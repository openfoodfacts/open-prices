# HOW TO install/test Open Prices API

## Prerequisites

* Python 3.11 (lower version may be OK, but untested)
* PostgreSQL 13 (lower version may be OK, but untested)

## Setup

```
# Clone repo
git clone https://github.com/openfoodfacts/open-prices.git
cd open-prices

# Copy .env.example to .env

```

### Without Docker

```
# Install poetry (Python dependency manager) at version 1.6.1
# see https://python-poetry.org/docs/

# Install dependencies (pyproject.toml)
poetry install

# Note: 
    All future commands should be prefixed with `poetry run`

# Apply migrations
python manage.py migrate

# Run Locally
python manage.py runserver

# Now server will run on http://127.0.0.1:8000/ but you can change the port as
python manage.py runserver 8001 
    Will run on http://127.0.0.1:8001/
```

### With Docker

::: Info
Open Prices now only supports docker compose v2 ( `docker compose` )
:::

create the dockers with

```sh
docker compose up
```

The sever should be running on <http://127.0.0.1:8000/>.

The run the migration of the database with

```sh
make migrate-db
```

Congrats, you can now contribute to the codebase :tada:
