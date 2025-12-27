#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   tools/publish/git_publish.sh 2025-12-26 "Commit message (optional)"
#
# Notes:
# - Uses repo-local venv if present: .venv/bin/python3
# - .env is ignored by git; md_to_html.py loads it via python-dotenv (override=True)

DATE="${1:-}"
MSG="${2:-}"

if [[ -z "${DATE}" ]]; then
  echo "ERROR: missing <DATE> argument (YYYY-MM-DD)"
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_ROOT}" ]]; then
  echo "ERROR: not inside a git repository"
  exit 2
fi
cd "${REPO_ROOT}"

echo "== Repo: ${REPO_ROOT}"
echo "== Date: ${DATE}"

MD="docs/log/${DATE}.md"
HTML="docs/log/${DATE}.html"
CMT="docs/log/comments/${DATE}_aristarkh.html"
INDEX="docs/log/index.html"

if [[ ! -f "${MD}" ]]; then
  echo "ERROR: missing markdown entry: ${MD}"
  exit 2
fi

echo "== Build site"

# Prefer project venv python if present
if [[ -x "${REPO_ROOT}/.venv/bin/python3" ]]; then
  PY="${REPO_ROOT}/.venv/bin/python3"
else
  PY="python3"
fi

echo "== Using python: $(${PY} -c 'import sys; print(sys.executable)')"

# Optional diag (shows mode/key presence without leaking key)
"${PY}" scripts/md_to_html.py --diag

echo "== Stage files"
git add \
  "${MD}" \
  "${HTML}" \
  "${INDEX}" || true

if [[ -f "${CMT}" ]]; then
  git add "${CMT}" || true
else
  echo "== Note: no comments file for this date (${CMT})"
fi

if git diff --cached --quiet; then
  echo "== Nothing to commit (already up to date)."
  exit 0
fi

if [[ -z "${MSG}" ]]; then
  MSG="Publish log ${DATE}"
fi

echo "== Commit: ${MSG}"
git commit -m "${MSG}"

echo "== Push"
git push

echo "== Done"
