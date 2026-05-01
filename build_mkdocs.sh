#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

mkdir -p docs/dev
cp CONTRIBUTING.md docs/dev/contributing.md
cp INSTALL.md docs/dev/install.md

# Build mkdocs
uv run mkdocs build --strict
