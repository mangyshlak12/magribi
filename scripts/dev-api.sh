#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source .env
set +a
exec .venv/bin/python apps/api/manage.py runserver 127.0.0.1:8000
