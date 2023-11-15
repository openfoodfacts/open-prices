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

# required packages to setup a virtualenv (optional, but recommended)
apt install python3-virtualenv virtualenv

# create and switch to virtualenv
python -m venv venv
source venv/bin/activate

# install
pip install -r requirements.txt
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
