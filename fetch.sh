#!/usr/bin/env bash
# Daglig henting: ./fetch.sh            (ser 7 dager tilbake)
#                 ./fetch.sh --days 30  (lengre tilbakeblikk)
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/python fetch.py "$@"
