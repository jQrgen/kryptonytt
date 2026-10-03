#!/usr/bin/env bash
# Daglig henting: ./fetch.sh            (ser 7 dager tilbake)
#                 ./fetch.sh --days 30  (lengre tilbakeblikk)
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/python fetch.py "$@"
# Samarbeid med Nordic Crypto om norske saker (bare forslag i køene, publiserer aldri)
.venv/bin/python tools/crosssite_handoff.py || echo "advarsel: crosssite_handoff feilet (hentingen er likevel ferdig)"
