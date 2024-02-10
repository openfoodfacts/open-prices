ARG PYTHON_VERSION=3.12

# base python setup
# -----------------
FROM python:$PYTHON_VERSION-slim as python-base
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
    POETRY_VERSION=1.6.1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
    ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# building packages
# -----------------
FROM python-base as builder-base
RUN curl -sSL https://install.python-poetry.org | python3 -
WORKDIR $PYSETUP_PATH
COPY poetry.lock  pyproject.toml ./
RUN poetry install --without dev

# This is our final image
# ------------------------
FROM python-base as runtime
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
    chown off:off -R /opt/open-prices /home/off
COPY --chown=off:off app /opt/open-prices/app
COPY --chown=off:off alembic /opt/open-prices/alembic

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY --chown=off:off poetry.lock pyproject.toml alembic.ini /opt/open-prices/

USER off:off
WORKDIR /opt/open-prices
ENTRYPOINT /docker-entrypoint.sh $0 $@

CMD ["uvicorn", "app.api:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]


# building dev packages
# ----------------------
FROM builder-base as builder-dev
WORKDIR $PYSETUP_PATH
COPY poetry.lock  pyproject.toml ./
# full install, with dev packages
RUN poetry install

# image with dev tooling
# ----------------------
# This image will be used by default, unless a target is specified in docker-compose.yml
FROM runtime as runtime-dev
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
