#!/usr/bin/env bash
# Reformat a JSON file in place with 2-space indent, UTF-8 preserved, trailing newline.
# Usage: ./fmt-json.sh path/to/file.json
set -euo pipefail

[[ $# -eq 1 ]] || { echo "usage: $0 <file.json>" >&2; exit 2; }
f=$1

python3 - "$f" <<'PY'
import json, sys
p = sys.argv[1]
with open(p) as fh:
    data = json.load(fh)
with open(p, 'w') as fh:
    json.dump(data, fh, indent=2, ensure_ascii=False)
    fh.write('\n')
PY
