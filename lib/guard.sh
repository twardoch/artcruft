#!/usr/bin/env bash
# this_file: lib/guard.sh
# Share clean-tree, version, quality and GitHub release checks.
set -euo pipefail

require_clean() {
    local status
    status=$(git status --porcelain)
    if [[ -n "$status" ]]; then
        printf 'Working tree must be clean:\n%s\n' "$status" >&2
        return 1
    fi
}

require_tagged_head() {
    local tag
    while IFS= read -r tag; do
        if [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            printf '%s\n' "$tag"
            return 0
        fi
    done < <(git tag --points-at HEAD --sort=-version:refname)
    echo 'HEAD must be exactly at a vMAJOR.MINOR.PATCH tag.' >&2
    return 1
}

run_gates() {
    uv run ruff check . && uv run ruff format --check . && uv run pytest -q
}

github_release() {
    local tag=$1 notes
    notes=$(mktemp)
    awk -v tag="$tag" '
        index($0, "## " tag " (") == 1 { found=1; next }
        found && /^## / { exit }
        found { print }
    ' CHANGELOG.md > "$notes"
    if gh release view "$tag" >/dev/null 2>&1; then
        gh release upload "$tag" dist/* --clobber
    else
        gh release create "$tag" dist/* --title "$tag" --notes-file "$notes"
    fi
    rm -f "$notes"
}

verify_dist_version() {
    uv run python - "${1#v}" dist/* <<'PY'
import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

expected, *files = sys.argv[1:]
for filename in files:
    path = Path(filename)
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            name, = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            metadata = archive.read(name)
    else:
        with tarfile.open(path) as archive:
            name, = [n for n in archive.getnames() if n.count("/") == 1 and n.endswith("/PKG-INFO")]
            metadata = archive.extractfile(name).read()
    version = BytesParser().parsebytes(metadata)["Version"]
    if version != expected:
        sys.exit(f"{path}: version {version!r} does not match {expected!r}")
print(f"Verified {len(files)} distributions at {expected}")
PY
}
