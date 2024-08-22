ARG PYTHON_VERSION=3.11

# base python setup
# -----------------
FROM python:$PYTHON_VERSION-slim AS python-base
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends -y curl && \
    apt-get autoremove --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
    ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# building packages
# -----------------
FROM python-base AS builder-base
RUN curl -sSL https://install.python-poetry.org | python3 -
WORKDIR $PYSETUP_PATH
COPY poetry.lock  pyproject.toml ./
RUN poetry install --without dev

# This is our final image
# ------------------------
FROM python-base AS runtime
COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
RUN poetry config virtualenvs.create false
ENV POETRY_VIRTUALENVS_IN_PROJECT=false

# create off user
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd -g $USER_GID off && \
    useradd -u $USER_UID -g off -m off && \
    mkdir -p /home/off && \
    mkdir -p /opt/open-prices && \
    mkdir -p /opt/open-prices/data && \
    mkdir -p /opt/open-prices/img && \
    mkdir -p /opt/open-prices/static && \
    chown off:off -R /opt/open-prices /home/off
COPY --chown=off:off config /opt/open-prices/config
COPY --chown=off:off open_prices /opt/open-prices/open_prices

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY --chown=off:off poetry.lock pyproject.toml manage.py /opt/open-prices/

USER off:off
WORKDIR /opt/open-prices
ENTRYPOINT /docker-entrypoint.sh $0 $@

RUN ["python", "manage.py", "collectstatic", "--noinput"]

CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "1"]


# building dev packages
# ----------------------
FROM builder-base AS builder-dev
WORKDIR $PYSETUP_PATH
COPY poetry.lock  pyproject.toml ./
# full install, with dev packages
RUN poetry install

# image with dev tooling
# ----------------------
# This image will be used by default, unless a target is specified in docker-compose.yml
FROM runtime AS runtime-dev
COPY --from=builder-dev $VENV_PATH $VENV_PATH
COPY --from=builder-dev $POETRY_HOME $POETRY_HOME
# Handle possible issue with Docker being too eager after copying files
RUN true
COPY .flake8 pyproject.toml ./
# create folders that we mount in dev to avoid permission problems
USER root
RUN \
    mkdir -p /opt/open-prices/.cov /opt/open-prices/docs /opt/open-prices/gh_pages && \
    chown -R off:off /opt/open-prices/.cov /opt/open-prices/docs /opt/open-prices/gh_pages
USER off
