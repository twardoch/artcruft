#!/usr/bin/env bash
# this_file: publish.sh
# Build and publish tagged workspace distributions to PyPI.
set -euo pipefail
cd "$(dirname "$0")"
source lib/guard.sh
BUMP=${1:-patch}
if [[ $# -gt 1 || ! "$BUMP" =~ ^(patch|minor|major)$ ]]; then
    echo 'Usage: ./publish.sh [patch|minor|major]' >&2
    exit 1
fi
if ! require_tagged_head >/dev/null 2>&1; then
    ./release.sh "$BUMP"
else
    require_clean
    run_gates
fi
TAG=$(require_tagged_head)
./build.sh
require_clean
verify_dist_version "$TAG"
if [[ ! ${UV_PUBLISH_TOKEN+x} && -f "$HOME/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$HOME/.env"
    set +a
fi
export UV_PUBLISH_TOKEN="${UV_PUBLISH_TOKEN:-${PYPI_TOKEN:-}}"
if [[ -z "$UV_PUBLISH_TOKEN" ]]; then
    echo 'Set UV_PUBLISH_TOKEN or PYPI_TOKEN before publishing.' >&2
    exit 1
fi
uv publish --check-url https://pypi.org/simple/ dist/*
