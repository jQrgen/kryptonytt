#!/usr/bin/env bash
# Nattrutine for Kryptonytt (inntak). Køyr ETTER Crypto Nordic si nattinnhenting (routines/nightly-fetch.sh i nordic-crypto).
# Ventar inntil NC_WAIT_MIN minutt (standard 45) på at Crypto Nordic-loggen for i dag er ferdig, og køyrer så ./fetch.sh
# (import frå Crypto Nordic + arrangementssøk + språksjekk). Publiserer ingenting. Logg: logs/nightly-YYYYMMDD.txt
set -uo pipefail
cd "$(dirname "$0")/.."
NC=${NORDIC_CRYPTO_DIR:-/workspace/nordic-crypto}
log="logs/nightly-$(date +%Y%m%d).txt"; mkdir -p logs
{
  echo "== Kryptonytt nattinntak $(date '+%Y-%m-%d %H:%M %Z')"
  nclog="$NC/logs/nightly-$(date +%Y%m%d).txt"
  for i in $(seq 1 "${NC_WAIT_MIN:-45}"); do grep -q "awaiting editor:" "$nclog" 2>/dev/null && break; [ "$i" = 1 ] && echo "ventar på Crypto Nordic ($nclog) ..."; sleep 60; done
  grep -q "awaiting editor:" "$nclog" 2>/dev/null && echo "Crypto Nordic ferdig: $(stat -c '%y' "$nclog" | cut -c1-16)" || echo "ÅTVARING: Crypto Nordic-innhentinga er ikkje ferdig – importerer det som finst"
  ./fetch.sh
  .venv/bin/python -c "import json;q=json.load(open('queue/review.json'));print('ventar på redaktøren:',len(q.get('items_needing_summary',[])),'saker,',len(q.get('nc_rejected',[])),'avviste hos Crypto Nordic,',len(q.get('events_pending',[])),'arrangement')" || true
} >>"$log" 2>&1
tail -8 "$log"
