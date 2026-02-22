# The build is currently made in 3 steps:
#
# 1. install all dependencies in a stage called `builder-base`. This stage (and all pre-install commands before)
#    is cached unless a dependency is updated. Only non-dev dependencies are installed.
# 2. build a stage called `runtime`: this is the production build. We create a user named `off` that will be used
#    when running the main command (we don't run as root inside containers). We make sure all directories that are
#    bind-mounted are owned by this user to prevent permission issues. In this stage, we also:
#      - copy the dependencies (`.venv`) installed in the previous build stage
#      - run `uv sync` again, to install the project (dependencies installed in the previous stage will be reused)
#      - add a docker entrypoint to automatically use the virtualenv interpreter
#      - collect Django static content and define the main command (running the API server)
# 3. build a stage called `runtime-dev`: this inherits from `runtime` but adds the following changes:
#      - install dev dependencies (useful to run linter, doc build,...)
#      - create some directories owned by the `off` user that are used when running dev commands, to prevent
#        permission issues
#   This is the build stage we use when developping locally.

ARG PYTHON_VERSION=3.11

# base python setup
# -----------------
FROM python:$PYTHON_VERSION-slim AS python-base

# Install uv globally
COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Enable bytecode compilation
    UV_COMPILE_BYTECODE=1 \
    # Copy from the cache instead of linking since it's a mounted volume
    UV_LINK_MODE=copy \
    # Ensure installed tools can be executed out of the box
    UV_TOOL_BIN_DIR=/usr/local/bin \
    # Ensure uv uses the system's python3
    PATH="/usr/local/bin:$PATH" \
    # Define which Python interpreter will be installed by uv
    UV_PYTHON=$PYTHON_VERSION
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends -y curl && \
    apt-get autoremove --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /opt/open-prices

# building packages
# -----------------
FROM python-base AS builder-base
# Install dependencies before copying the rest of the code to leverage Docker cache
# We use the `--no-install-project` option to prevent uv from installing the project.
# Since the project changes frequently, but its dependencies are generally static, this
# can be a big time saver.
# See https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers for more
# info
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# This is our final image
# ------------------------
FROM python-base AS runtime

# create off user
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd -g $USER_GID off && \
    useradd -u $USER_UID -g off -m off

# Create some directories for which the off user need write permissions
RUN mkdir -p /home/off/.cache && \
    chown off:off -R /home/off && \
    mkdir -p /opt/open-prices && \
    mkdir -p /opt/open-prices/img
RUN chown off:off -R /opt/open-prices

# Copy the full repo in the workdir
COPY --chown=off:off . /opt/open-prices

# Copy the virtualenv containing dependencies installed in the previous stage
COPY --chown=off:off --from=builder-base /opt/open-prices/.venv /opt/open-prices/.venv
# Final sync to install the project itself if needed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT /docker-entrypoint.sh $0 $@

RUN ["uv", "run", "--no-dev", "python", "manage.py", "collectstatic", "--noinput"]

CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "1"]


FROM runtime AS runtime-dev
# building dev packages
# ----------------------
# full install, with dev packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group dev

# image with dev tooling
# ----------------------
# create folders that we mount in dev to avoid permission problems
USER root
RUN \
    mkdir -p /opt/open-prices/.cov /opt/open-prices/docs /opt/open-prices/gh_pages && \
    chown -R off:off /opt/open-prices/.cov /opt/open-prices/docs /opt/open-prices/gh_pages
USER off
