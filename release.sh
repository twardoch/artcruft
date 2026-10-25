#!/usr/bin/env bash
# this_file: release.sh
# Gate, version and build a GitHub release through gitnextver.
set -euo pipefail
cd "$(dirname "$0")"
source lib/guard.sh
BUMP=${1:-patch}
if [[ $# -gt 1 || ! "$BUMP" =~ ^(patch|minor|major)$ ]]; then
    echo 'Usage: ./release.sh [patch|minor|major]' >&2
    exit 1
fi
require_clean
run_gates
git fetch --tags --quiet
NEXT=$(git tag | uvx --from gitnextver python -c '
import sys
from gitnextver.versioning import next_version
print(next_version(sys.stdin.read().splitlines(), bump=sys.argv[1], initial="v0.1.0"))
' "$BUMP")
uv run python - "$NEXT" <<'PY'
import re
import sys
from datetime import date
from pathlib import Path

path = Path("CHANGELOG.md")
text, count = re.subn(
    r"^## Unreleased[ \t]*$",
    f"## Unreleased\n\n## {sys.argv[1]} ({date.today().isoformat()})",
    path.read_text(), count=1, flags=re.MULTILINE,
)
if not count:
    sys.exit("CHANGELOG.md must contain a ## Unreleased heading")
path.write_text(text)
PY
if ! TAG=$(uvx gitnextver --bump "$BUMP"); then
    git checkout -- CHANGELOG.md
    exit 1
fi
if [[ "$TAG" != "$NEXT" ]]; then
    printf 'gitnextver returned %s; expected %s\n' "$TAG" "$NEXT" >&2
    exit 1
fi
require_clean
HEAD_TAG=$(require_tagged_head)
[[ "$HEAD_TAG" == "$TAG" ]]
./build.sh
require_clean
github_release "$TAG"
