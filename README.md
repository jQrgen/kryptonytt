# Kryptonytt Norge

Norske nyheter om bitcoin, blokkjede og krypto, et organisasjonskart («Hvem er hvem i norsk krypto») og en kalender over norske kryptoarrangementer.
Nettsted: https://jqrgen.github.io/kryptonytt/ · Skjermmodus for kontorskjerm: https://jqrgen.github.io/kryptonytt/skjerm/

## Slik virker det

```
Nordic Crypto (routines/nightly-fetch.sh, 03:41)  ──►  nordic-crypto/data/news.json (country NO)
                                                          │  tools/import_nordic_crypto.py  (./fetch.sh)
                                                          ▼
                              data/news.json, queue/review.json   (venter på redaksjonen, med utkast fra Nordic Crypto)
                                                          │
                              redaksjonen skriver queue/approved.json
                                                          ▼
build.sh  ──►  site/  (bare godkjent innhold)  ──►  personverngrind  ──►  publish.sh --yes  ──►  gh-pages
```

1. **Inntak** (`./fetch.sh` / `routines/nightly-intake.sh`, hver natt **etter** Nordic Crypto): Kryptonytt henter og researcher
   ikke lenger nyheter selv. Nordic Crypto gjør innhentingen for hele Norden (Kryptonytts kilder er slått inn i
   `nordic-crypto/sources.json`, merket `country: NO`, `merged_from: kryptonytt`), og `tools/import_nordic_crypto.py` henter
   de norske sakene (`country == "NO"`) inn hit: tittel, URL, utgiver, dato, betalingsmur, tema, Nordic Crypto-status
   (`nc` + `nc_verification`: godkjent/avvist/venter, `approved_by/at`, `reject_reason`), engelsk sammendrag og nn/nb-oversettelse
   som **utkast** i køraden (`utkast_frå_nordic_crypto`), kilder (`seen_via`) og bilder bare med lisens og kreditering.
   Dedup på normalisert URL og tittel; idempotent (kjøres den på nytt, oppdateres bare status og utkast). Kryptonytts egne
   avgjørelser i `queue/approved.json` endres aldri. Saker Nordic Crypto har avvist, får status `rejected` (`rejected_by: Nordic Crypto`)
   og listes i `queue/review.json` → `nc_rejected`; vil redaksjonen likevel ha en, legges den i `approved.json` som vanlig.
   Arrangementssøket (`fetch.py --events-only`, kalender og «Tidligere arrangementer») er fortsatt Kryptonytts eget.
   Gammel egen henting finnes fortsatt: `./fetch.sh --legacy-fetch [--days N]` (RSS + nyhetssøk som før, følger robots.txt,
   minst 2 s mellom forespørsler per nettsted, aldri artikkeltekst bak betalingsmur; kilder i `sources.json`).
2. **Redaksjon**: alle nye saker og arrangementer får status `pending`. Redaksjonen skriver en egen oppsummering på 1–2 setninger
   og godkjenner i `queue/approved.json`. Arrangementer tas bare med når arrangørens egen side eller en offentlig oppføring viser
   dato, sted og arrangør, og arrangementet faktisk handler om krypto, bitcoin eller blokkjede. Betalte og sponsede er merket.
3. **Bygging** (`./build.sh`): leser industrikart-eksporten og `data/orgchart_extra.json`, slår inn godkjenningene og lager statisk HTML i `site/`.
   En personverngrind (`tools/privacy_gate.py`) stopper byggingen hvis noe ligner e-post, telefonnummer, fødselsnummer, kontonummer o.l.
4. **Publisering** (`./publish.sh --yes`): pusher `site/` til grenen `gh-pages`. Uten `--yes` bygges og sjekkes det bare.

## Kommandoer

| Hva | Kommando |
|---|---|
| Nattinntak (rutine) | `routines/nightly-intake.sh` (venter på Nordic Crypto-loggen, kjører `./fetch.sh`; logg `logs/nightly-YYYYMMDD.txt`) |
| Hent nyheter (fra Nordic Crypto) og arrangementer | `./fetch.sh` (valg: `--days N` tilbakeblikk for nye saker, `--dry-run`; `KN_EVENTS=0` hopper over arrangementer) |
| Gammel egen henting (reserve) | `./fetch.sh --legacy-fetch` (valg: `--days N`, `--only id1,id2`, `--no-events`) |
| Legg til en sak manuelt | `./fetch.sh --add URL --source-name "Navn" --date YYYY-MM-DD --title "Tittel"` (valgfritt `--origin "tips fra Nordic Crypto"`: intern merknad i køen, vises aldri offentlig) |
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


## Språk (nynorsk, bokmål, engelsk)

- Nynorsk er hovudspråket og ligg på standardadressene. Bokmål ligg under `/bm/`, engelsk under `/en/`. `build.py` byggjer alle tre (sidetekstar i `tools/site_pages.py` og `tools/site_pages2.py`, skrivne som `L(nynorsk, bokmål, engelsk)`).
- Språkvalet i toppen set førstepartsinformasjonskapselen `kn_lang` (path=/kryptonytt/, SameSite=Lax, 1 år). Han blir berre brukt når nokon kjem utanfrå til ei nynorsk-side; direkte lenkjer til `/bm/` og `/en/` blir aldri omdirigerte, og eit klikk på eit språk vinn alltid. Test: `.venv/bin/python tools/i18n_check.py` (køyrer òg i `publish.sh`), skjermbilete med `--shots`.
- **Redaktøren** skriv kvar godkjende sak i tre variantar i `queue/approved.json`: `summary` (bokmål), `summary_nn`, `summary_en`; eigne titlar `title`/`title_nn`/`title_en` berre når vi sjølve har omsett tittelen; lenkjetekstar `label`/`label_nn`/`label_en`; arrangementsmerknader `events.notes`/`notes_nn`/`notes_en`; endringslogg `text`/`text_nn`/`text_en`. Eksterne titlar og sitat står som i kjelda.
- **Nattrutinen** (`fetch.sh`) og **morgonrutinen** (`publish.sh`) køyrer `tools/check_i18n.py`, som legg det som manglar i `queue/review.json` -> `translations_needed`. Manglar ein variant, viser sida bokmål med `lang="nb"`.
- **Researcheren** kan levere skildringar på bokmål som før; organisasjonskart- og Akademia-skildringar blir viste på bokmål (merkte `lang="nb"`) på nynorsk- og engelsksidene til vi har omsette felt.
- Skriv «kunstig intelligens» (engelsk «artificial intelligence»), aldri AI eller KI.

## Forslag til organisasjonskartet (pending)
`data/orgchart_pending.json` holder nye aktører, personer (Brønnøysund-roller: bare navn og rolle) og profillenker som venter på redaktøren.
`tools/import_industrikart.py` tar dem inn med status `pending`; `tools/apply_approvals.py` publiserer dem bare når id-en står i
`queue/approved.json` → `entities.approve` / `profiles.approve` (avvis med `.reject`), og lister alt som venter i `queue/review.json` → `org_pending` / `profiles_pending`.
Kategorien «Internasjonale aktørar i Noreg» (`industry: "internasjonal"`) er for globale aktører med verifiserbar norsk aktivitet.
Kildesjekken for Kaupr-aktørene står i `research/kaupr-kildesjekk.md`. Kaupr er sponsor og kilde; industrikartet viser en opplysningsmerknad når en publisert aktør har Kaupr som kilde.

## Nyheitsbrev (Substack + e-post) – førebudd, AV
`newsletter/substack-setup.md` (namn, underdomene, tekstar på nynorsk og bokmål, profilbilete i `newsletter/assets/`,
velkomst-e-post, mal for vekesamandrag, Kaupr-opplysning, sjekkliste for jQrgen). `newsletter/digest.py` lagar
vekesamandraget berre frå publiserte saker. Påmeldingsskjemaet (botnen av kvar side + `/nyhetsbrev/`, nn/nb/en, med
personvernmerknad) ligg i `tools/newsletter_site.py` og er av til `newsletter/config.json` har `enabled: true`; det sender til
tipworker i Nordic Crypto-repoet (`/api/subscribe`, `site=kryptonytt`, dobbel stadfesting). Ingenting blir sendt, og det finst
ingen Substack-konto før jQrgen opprettar han.

