#!/usr/bin/env bash
# this_file: build.sh
# Build the six pure-Python workspace distributions.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf dist
uv build --all-packages -o dist
ls -lh dist
