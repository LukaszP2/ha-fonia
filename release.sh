#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: ./release.sh <version> [description]"
    echo "Example: ./release.sh 0.1.0 'First stable release'"
    exit 1
fi

NEW_VER="$1"
MSG="${2:-Release v${NEW_VER}}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${REPO_DIR}/custom_components/fonia/manifest.json"
CONST_FILE="${REPO_DIR}/custom_components/fonia/const.py"

python3 -c "
import json
import re

with open('${MANIFEST}', 'r+') as f:
    d = json.load(f)
    d['version'] = '${NEW_VER}'
    f.seek(0)
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write('\n')
    f.truncate()

with open('${CONST_FILE}', 'r+') as f:
    content = f.read()
    content = re.sub(r'VERSION = \"[^\"]+\"', f'VERSION = \"${NEW_VER}\"', content)
    f.seek(0)
    f.write(content)
    f.truncate()
"

if [ -d "${REPO_DIR}/blueprints/automation/fonia" ]; then
    mkdir -p "${REPO_DIR}/custom_components/fonia/blueprints"
    for f in "${REPO_DIR}/blueprints/automation/fonia/"*.yaml; do
        target="${REPO_DIR}/custom_components/fonia/blueprints/$(basename "$f")"
        if [ ! -e "$target" ] || ! cmp -s "$f" "$target"; then
            cp --remove-destination -f "$f" "$target"
        fi
    done
fi

echo "Running code checks and test suite..."
ruff check . --fix
pytest -q

git -C "${REPO_DIR}" add .
git -C "${REPO_DIR}" commit -m "Bump version to ${NEW_VER}: ${MSG}" || true
git -C "${REPO_DIR}" tag -a "v${NEW_VER}" -m "${MSG}"
git -C "${REPO_DIR}" push origin HEAD --follow-tags
echo "Release v${NEW_VER} successfully pushed to GitHub!"
