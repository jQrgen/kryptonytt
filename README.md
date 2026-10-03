# Kryptonytt Norge

Norske nyheter om bitcoin, blokkjede og krypto, et organisasjonskart («Hvem er hvem i norsk krypto») og en kalender over norske kryptoarrangementer.
Nettsted: https://jqrgen.github.io/kryptonytt/ · Skjermmodus for kontorskjerm: https://jqrgen.github.io/kryptonytt/skjerm/

## Slik virker det

```
fetch.sh  ──►  data/news.json, data/events.json  ──►  queue/review.json   (venter på redaksjonen)
                                                          │
                              redaksjonen skriver queue/approved.json
                                                          ▼
build.sh  ──►  site/  (bare godkjent innhold)  ──►  personverngrind  ──►  publish.sh --yes  ──►  gh-pages
```

1. **Henting** (`./fetch.sh`, hver natt): leser RSS-feeder fra norske aviser, myndigheter, blogger og podkaster, et nyhetssøk
   avgrenset til norske domener, og arrangementssider (JSON-LD/iCal). Følger robots.txt, egen brukeragent, minst 2 s mellom
   forespørsler per nettsted. Henter aldri artikkeltekst bak betalingsmur. Kilder står i `sources.json`.
2. **Redaksjon**: alle nye saker og arrangementer får status `pending`. Redaksjonen skriver en egen oppsummering på 1–2 setninger
   og godkjenner i `queue/approved.json`. Arrangementer tas bare med når arrangørens egen side eller en offentlig oppføring viser
   dato, sted og arrangør, og arrangementet faktisk handler om krypto, bitcoin eller blokkjede. Betalte og sponsede er merket.
3. **Bygging** (`./build.sh`): leser industrikart-eksporten og `data/orgchart_extra.json`, slår inn godkjenningene og lager statisk HTML i `site/`.
   En personverngrind (`tools/privacy_gate.py`) stopper byggingen hvis noe ligner e-post, telefonnummer, fødselsnummer, kontonummer o.l.
4. **Publisering** (`./publish.sh --yes`): pusher `site/` til grenen `gh-pages`. Uten `--yes` bygges og sjekkes det bare.

## Kommandoer

| Hva | Kommando |
|---|---|
| Hent nyheter og arrangementer | `./fetch.sh` (valg: `--days N`, `--only id1,id2`, `--no-events`) |
| Legg til en sak manuelt | `./fetch.sh --add URL --source-name "Navn" --date YYYY-MM-DD --title "Tittel"` |
| Legg til et arrangement | `.venv/bin/python events.py --add-event URL` (evt. `--title --start --place --organiser --paid ja`) |
| Bygg og sjekk | `./build.sh` |
| Publiser | `./publish.sh --yes` |

Oppsett: `python3 -m venv .venv && .venv/bin/pip install feedparser requests beautifulsoup4 lxml` (pluss `playwright` for skjermbilder i `tools/screens.py`).

## Hva som ikke ligger i repoet

`data/`, `state/`, `queue/`, `logs/` og `site/` er arbeidsdata og holdes utenfor git (se `.gitignore`). Det publiserte nettstedet ligger på grenen `gh-pages`.

## Rettigheter

- Koden er MIT-lisensiert (se `LICENSE`).
- Dataene og oppsummeringene på nettstedet er Kryptonytt Norges egne.
- Lenkede artikler tilhører utgiverne. Bilder fra tredjeparter tilhører rettighetshaverne og brukes etter lisensen som er oppgitt ved hvert bilde (Wikimedia Commons: CC0, CC BY, CC BY-SA).
- Ingenting på nettstedet er investeringsråd.

Rettelser og fjerning: opprett en sak på https://github.com/jQrgen/kryptonytt/issues.
