#!/usr/bin/env bash
# Bygger site/, kjører personverngrinda og publiserer KUN site/ til gh-pages i jQrgen/kryptonytt.
# Koden (ikke data/, state/, queue/, logs/) pushes til main.
# Bruk:  ./publish.sh         -> bare bygg + personverngrind (ingenting pushes)
#        ./publish.sh --yes   -> bygg, sjekk og publiser (kun etter at jQrgen har godkjent)
set -euo pipefail
cd "$(dirname "$0")"
DRY=${1:-}
REPO=https://github.com/jQrgen/kryptonytt.git
URL=https://jqrgen.github.io/kryptonytt/
.venv/bin/python tools/check_i18n.py || true   # åtvarar om nynorsk/engelsk manglar (bokmål blir då vist)
.venv/bin/python build.py
.venv/bin/python tools/i18n_check.py || { echo "språktest feila – publiserer ikkje"; exit 1; }
.venv/bin/python tools/privacy_gate.py site
[ "$DRY" = "--yes" ] || { echo "Bygget og sjekket lokalt. Ikke publisert (kjør ./publish.sh --yes for å publisere)."; exit 0; }
git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REPO"
# 1) gh-pages: egen klon i .publish/ som bare inneholder site/
if [ ! -d .publish/.git ]; then
  rm -rf .publish
  if git ls-remote --exit-code --heads "$REPO" gh-pages >/dev/null 2>&1; then git clone -q --branch gh-pages --single-branch "$REPO" .publish
  else mkdir .publish && git -C .publish init -q -b gh-pages && git -C .publish remote add origin "$REPO"; fi
fi
git -C .publish config user.name "$(git config user.name)"; git -C .publish config user.email "$(git config user.email)"
git -C .publish pull -q --ff-only origin gh-pages 2>/dev/null || true
find .publish -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} + && cp -a site/. .publish/
git -C .publish add -A
if git -C .publish diff --cached --quiet; then echo "gh-pages: ingen endringer"; else
  git -C .publish commit -q -m "Publiser $(date '+%Y-%m-%d %H:%M %Z')" && git -C .publish push -q origin gh-pages && echo "gh-pages: pushet"; fi
# Artikkelarkiv: før opp alt som no er publisert (berre tillegg, aldri sletting; archive/articles.db + archive/articles.json)
.venv/bin/python tools/article_archive.py record || echo "advarsel: artikkelarkivet vart ikkje oppdatert"
# 2) main: bare kode og konfig (se .gitignore)
git add -A && { git diff --cached --quiet || git commit -q -m "Oppdater pipeline $(date '+%Y-%m-%d')"; } && git push -q origin main || echo "advarsel: push av main feilet"
# 3) sjekk at siden svarer
for i in $(seq 1 30); do code=$(curl -s -o /dev/null -w '%{http_code}' "$URL" || true); [ "$code" = 200 ] && break; sleep 10; done
echo "live: $URL -> HTTP $code"
