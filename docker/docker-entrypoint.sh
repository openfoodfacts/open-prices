#!/bin/bash

set -e

# activate our virtual environment here
. /opt/open-prices/.venv/bin/activate

PRE_ARGS=()

# You can put other setup logic here

# Evaluating passed command:
exec "${PRE_ARGS[@]}" "$@"
