#!/bin/bash

set -euo pipefail
IFS=$'\n\t'


# Build mkdocs
poetry run mkdocs build --strict
