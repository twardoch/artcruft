#!/usr/bin/env bash
# this_file: install.sh
# Install the complete workspace with development dependencies and extras.
set -euo pipefail
cd "$(dirname "$0")"
uv sync --all-packages --all-extras
