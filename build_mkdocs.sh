#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

mkdir -p docs/dev
cp --remove-destination CONTRIBUTING.md docs/dev/contributing.md
cp --remove-destination INSTALL.md docs/dev/install.md

# Build mkdocs
uv run mkdocs build --strict
