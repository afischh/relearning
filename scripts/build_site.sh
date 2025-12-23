#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

source .venv/bin/activate

python scripts/md_to_html.py
echo "OK: site rebuilt"
