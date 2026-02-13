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
    VENV_PATH=/opt/open-prices/.venv \
    UV_PATH=/root/.local/bin/uv
ENV PATH="/root/.local/bin:/opt/open-prices/.venv/bin:$PATH"

# building packages
# -----------------
FROM python-base AS builder-base
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
WORKDIR /opt/open-prices
COPY uv.lock pyproject.toml README.md ./
RUN uv sync --frozen

# This is our final image
# ------------------------
FROM python-base AS runtime
COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY --from=builder-base $UV_PATH $UV_PATH

# create off user
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd -g $USER_GID off && \
    useradd -u $USER_UID -g off -m off && \
    mkdir -p /home/off && \
    mkdir -p /home/off/.cache && \
    mkdir -p /opt/open-prices && \
    mkdir -p /opt/open-prices/data && \
    mkdir -p /opt/open-prices/img && \
    mkdir -p /opt/open-prices/static && \
    chown off:off -R /opt/open-prices /home/off
COPY --chown=off:off config /opt/open-prices/config
COPY --chown=off:off open_prices /opt/open-prices/open_prices

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY --chown=off:off uv.lock pyproject.toml manage.py /opt/open-prices/

USER off:off
WORKDIR /opt/open-prices
ENTRYPOINT /docker-entrypoint.sh $0 $@

RUN ["python", "manage.py", "collectstatic", "--noinput"]

CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "1"]


# building dev packages
# ----------------------
FROM builder-base AS builder-dev
WORKDIR /opt/open-prices
COPY uv.lock pyproject.toml README.md ./
# full install, with dev packages
RUN uv sync --frozen --group dev

# image with dev tooling
# ----------------------
# This image will be used by default, unless a target is specified in docker-compose.yml
FROM runtime AS runtime-dev
COPY --from=builder-dev $VENV_PATH $VENV_PATH
COPY --from=builder-dev $UV_PATH $UV_PATH
# Handle possible issue with Docker being too eager after copying files
RUN true
COPY pyproject.toml ./
# create folders that we mount in dev to avoid permission problems
USER root
RUN \
    mkdir -p /opt/open-prices/.cov /opt/open-prices/docs /opt/open-prices/gh_pages && \
    chown -R off:off /opt/open-prices/.cov /opt/open-prices/docs /opt/open-prices/gh_pages
USER off
