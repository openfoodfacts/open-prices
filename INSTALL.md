# HOWTO install/test Open Prices API

## Prerequisites

- Python 3.12
- pip

## Setup

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

## Run locally

```
uvicorn app.api:app --reload
```
or use `--host` if you want to make it available on your local network, eg.:
```
uvicorn app.api:app --reload --host 192.168.0.100
```
