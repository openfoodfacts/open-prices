#!/bin/bash

set -euo pipefail
IFS=$'\n\t'


# Build mkdocs
uv run mkdocs build --strict
