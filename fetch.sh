#!/usr/bin/env bash
# Nattleg inntak for Kryptonytt Norge.
#   ./fetch.sh                 standard (frå 4. okt. 2026): norske saker frå Crypto Nordic (tools/import_nordic_crypto.py)
#                              + Kryptonytt sitt eige arrangementssøk (kalender, «Tidlegare arrangement»). Hentar/researchar ikkje nyheiter sjølv.
#   ./fetch.sh --legacy-fetch [--days N]   gammal eiga innhenting (fetch.py: RSS + nyheitssøk) + crosssite_handoff, som før
#   ./fetch.sh --add URL ...   legg til éi sak manuelt (fetch.py --add, som før)
#   KN_EVENTS=0 ./fetch.sh     hopp over arrangementssøket
# Publiserer aldri.
set -euo pipefail
cd "$(dirname "$0")"
if [ "${1:-}" = "--legacy-fetch" ] || [ "${KN_INTAKE:-nordic}" = "legacy" ]; then
  [ "${1:-}" = "--legacy-fetch" ] && shift
  .venv/bin/python fetch.py "$@"
  # Samarbeid med Crypto Nordic om norske saker (bare forslag i køene, publiserer aldri)
  .venv/bin/python tools/crosssite_handoff.py || echo "advarsel: crosssite_handoff feilet (hentingen er likevel ferdig)"
elif printf '%s\n' "$@" | grep -qx -- "--add"; then
  .venv/bin/python fetch.py "$@"
else
  # Nyheiter: Crypto Nordic sine norske saker (med kjelder, verifiseringsstatus og utkast) -> data/news.json + queue/review.json
  .venv/bin/python tools/import_nordic_crypto.py --require-fresh "$@" || echo "advarsel: import frå Crypto Nordic melde feil/gammal Crypto Nordic-innhenting (sjå over)"
  [ "${KN_EVENTS:-1}" = "0" ] || .venv/bin/python fetch.py --events-only || echo "advarsel: arrangementssøket feila"
fi
# Språk: nye saker treng oppsummering på bokmål, nynorsk og engelsk. Lista kjem i queue/review.json -> translations_needed.
.venv/bin/python tools/check_i18n.py || true
