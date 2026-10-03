#!/usr/bin/env bash
# Bygger site/ og kjører personverngrinda. Pusher ingenting.
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/python build.py
.venv/bin/python tools/privacy_gate.py site
