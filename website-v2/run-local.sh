#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/backend"
if [ ! -x .venv/bin/python ]; then
  echo 'Create backend/.venv and install requirements.lock.txt first; see DASHBOARD.md.' >&2
  exit 1
fi
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
