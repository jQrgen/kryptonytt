# Kryptonytt Norge – oppsett for nyheitsbrev (Substack + e-post)

Status: **førebudd, ingenting er oppretta eller sendt.** Det finst ingen Substack-konto enno; jQrgen opprettar han med si eiga
innlogging. Ingenting her er publisert til gh-pages, og påmeldingsskjemaet på nettstaden er **av**
(`newsletter/config.json` → `enabled: false`). Synleg norsk tekst seier alltid «kunstig intelligens», aldri AI eller KI.

To kanalar:
1. **Substack** – sjølve publikasjonen (nettarkiv + e-post og app frå Substack).
2. **E-postpåmelding på nettstaden** – eige skjema med dobbel stadfesting → Cloudflare Worker (`tipworker/` i
   Crypto Nordic-repoet, `POST /api/subscribe` med `site=kryptonytt`) → D1-tabellen `subscribers`. Stadfesta adresser blir
   eksporterte som CSV (`tipworker/export_subscribers.py --site kryptonytt`) og importerte i Substack, eller sende med ein
   annan leverandør seinare (ikkje valt).

---

## 1. Publikasjon

| Felt | Forslag |
|---|---|
| Namn på publikasjonen | **Kryptonytt Norge** |
| Underdomene | **kryptonyttnorge.substack.com** – såg ledig ut 4. okt. 2026 kl. 01.22 (HTTP 404, som for eit tilfeldig ubrukt namn). **kryptonytt.substack.com er opptatt:** adressa sender vidare (HTTP 301) til finuntium.substack.com, «Finuntium» av Alexander Ellefsen – eit norsk nyheitsbrev om bitcoin og finans. Namnet «Kryptonytt» har altså vore brukt på Substack før; vurder om det kan skape forveksling. Andre ledige alternativ (404): kryptonyttno, kryptonyheiter. Endeleg svar får du først i registreringsskjemaet til Substack. |
| Språk (Settings › Publication details) | Norsk |
| Avsendarnamn («From») | **Kryptonytt Norge** |
| Svaradresse | jQrgen avgjer (det finst inga offentleg e-postadresse i dag; ikkje bruk ei privat adresse utan å ha bestemt det) |
| Betalt abonnement | av (gratis nyheitsbrev) |
| Kategoriar | Hovudkategori **Crypto**; deretter **Finance** og **News** (vel frå den gjeldande lista til Substack) |

**Slagord (≤ 100 teikn):**
- nn: Norske nyheiter om bitcoin, blokkjede og krypto – kort samandrag kvar veke.
- nb: Norske nyheter om bitcoin, blokkjede og krypto – kort sammendrag hver uke.
- en (om nødvendig): Norwegian news about bitcoin, blockchain and crypto – a short weekly digest.

**Om-side (nynorsk):**
> Kryptonytt Norge samlar norske nyheiter om bitcoin, blokkjede og krypto – frå aviser, styresmakter, bloggar og
> podkastar – og gir kvar sak eit kort samandrag med lenkje til kjelda. Ein gong i veka sender dette nyheitsbrevet sakene
> redaktøren vår har godkjent.
>
> Kryptonytt Norge blir driven av Jørgen S. Notland (jQrgen), Oslo, med hjelp av kunstig intelligens. Ansvarleg redaktør er
> «Kryptonytt redaktør», ein bot basert på kunstig intelligens, med jQrgen som ansvarleg person. Ingenting her er
> investeringsråd. På nettstaden finn du òg ein kalender og ei oversikt over kven er kven i norsk krypto:
> https://jqrgen.github.io/kryptonytt/
>
> Openheit: Kaupr (kaupr.io) er sponsor av Kryptonytt og ei av kjeldene våre.

**Om-side (bokmål):**
> Kryptonytt Norge samler norske nyheter om bitcoin, blokkjede og krypto – fra aviser, myndigheter, blogger og podkaster –
> og gir hver sak et kort sammendrag med lenke til kilden. Én gang i uka sender dette nyhetsbrevet sakene redaktøren vår
> har godkjent.
>
> Kryptonytt Norge drives av Jørgen S. Notland (jQrgen), Oslo, med hjelp av kunstig intelligens. Ansvarlig redaktør er
> «Kryptonytt redaktør», en bot basert på kunstig intelligens, med jQrgen som ansvarlig person. Ingenting her er
> investeringsråd. På nettstedet finner du også en kalender og en oversikt over hvem er hvem i norsk krypto:
> https://jqrgen.github.io/kryptonytt/bm/
>
> Åpenhet: Kaupr (kaupr.io) er sponsor av Kryptonytt og en av kildene våre.

## 2. Profil (frå det eksisterande uttrykket på nettstaden: ordmerket «Krypto**nytt** Norge» i #b45309 og «K»-ikonet)

| Felt i Substack | Fil |
|---|---|
| Logo (kvadratisk, ≥ 256 px) | `newsletter/assets/logo-512.png` (kjelde `logo.svg`) |
| Ordmerke (valfritt) | `newsletter/assets/wordmark-1200x300.png` |
| Toppbilete i e-post | `newsletter/assets/email-banner-1100x220.png` |
| Forsidebilete / delingsbilete | `newsletter/assets/cover-1200x630.png` |

Lag på nytt med `.venv/bin/python newsletter/make_brand_assets.py` (Crypto Nordic-repoet; lagar bileta for begge stadene).
Framheva farge i Substack-temaet: **#b45309**.

## 3. Velkomst-e-post (Substack: Settings › Emails › Welcome email) – utkast

**Emne (nn):** Velkomen til Kryptonytt Norge

> Hei, og takk for at du abonnerer.
>
> Ein gong i veka får du eit kort samandrag av norske nyheiter om bitcoin, blokkjede og krypto som redaktøren vår har
> godkjent – overskrift, eitt eller to setningar og lenkje til kjelda. Nokre kjelder kan krevje abonnement; det står i så
> fall ved saka.
>
> Samandraga er skrivne av «Kryptonytt redaktør», ein bot basert på kunstig intelligens, og Jørgen S. Notland (jQrgen) i
> Oslo er ansvarleg person. Ingenting i nyheitsbrevet er investeringsråd. Ser du ein feil eller ei sak vi har gått glipp
> av? Skriv til oss på GitHub: https://github.com/jQrgen/kryptonytt/issues
>
> Openheit: Kaupr (kaupr.io) er sponsor av Kryptonytt og ei av kjeldene våre.
>
> Du kan melde deg av når du vil med lenkja nedst i kvar e-post.
>
> – Kryptonytt Norge

**Emne (nb):** Velkommen til Kryptonytt Norge

> Hei, og takk for at du abonnerer.
>
> Én gang i uka får du et kort sammendrag av norske nyheter om bitcoin, blokkjede og krypto som redaktøren vår har
> godkjent – overskrift, én eller to setninger og lenke til kilden. Noen kilder kan kreve abonnement; det står i så fall
> ved saken.
>
> Sammendragene er skrevet av «Kryptonytt redaktør», en bot basert på kunstig intelligens, og Jørgen S. Notland (jQrgen) i
> Oslo er ansvarlig person. Ingenting i nyhetsbrevet er investeringsråd. Ser du en feil eller en sak vi har gått glipp av?
> Skriv til oss på GitHub: https://github.com/jQrgen/kryptonytt/issues
>
> Åpenhet: Kaupr (kaupr.io) er sponsor av Kryptonytt og en av kildene våre.
>
> Du kan melde deg av når du vil med lenken nederst i hver e-post.
>
> – Kryptonytt Norge

(Stadfestings- og velkomst-e-postane til påmeldinga på nettstaden ligg i `tipworker/src/messages.js` i Crypto Nordic-repoet, på nynorsk, bokmål og engelsk.)

## 4. Vekesamandrag (laga berre frå godkjende saker)

    .venv/bin/python build.py                                  # bygg site/ (berre publiserte saker)
    .venv/bin/python newsletter/digest.py --lang nn            # siste 7 dagar fram til i dag (Oslo-tid)
    .venv/bin/python newsletter/digest.py --lang nb --until 2026-10-03

- Les `site/data/news.json`, der berre publiserte saker med eiga oppsummering er med. Skriv
  `newsletter/out/digest-<dato>-<språk>.md|.txt|.html` (gitignored).
- `.md` → lim inn i eit nytt Substack-innlegg. `.html`/`.txt` → for ein e-postleverandør (`{{unsubscribe}}` = lenkja for å melde seg av).
- Mal (kvar utgåve):
  1. Tittel «Kryptonytt Norge – veka som gjekk» (nb: «uka som gikk») + datoar, éi innleiingslinje
  2. Sakene, nyaste først: **overskrift (lenkje til kjelda)** slik ho står hos kjelda, så samandraget vårt på utgåvespråket,
     så `kjelde · dato · kan krevje abonnement · Kaupr er sponsor` (det siste berre for saker frå Kaupr)
  3. Lenkje til nettstaden (alle saker, kalender, kven er kven)
  4. Botn: Kaupr-opplysning, kven som driv staden (med hjelp av kunstig intelligens), ingen investeringsråd, kvifor du får e-posten
- Norsk tekst blir sjekka for «AI»/«KI» i vår eigen tekst før fila blir skriven (overskrifter frå kjeldene står som publisert).
- Døme: `newsletter/sample-digest-2026-10-03-nn.md`.
- Forslag til rytme: kvar veke, fredag morgon. Ingenting er planlagt automatisk; jQrgen eller redaktøren limer inn og sender.

## 5. Kaupr-opplysning (brukast overalt: om-sida, velkomst-e-posten og botnen i kvart vekesamandrag)

- nn: Openheit: Kaupr (kaupr.io) er sponsor av Kryptonytt og ei av kjeldene våre.
- nb: Åpenhet: Kaupr (kaupr.io) er sponsor av Kryptonytt og en av kildene våre.
- en: Disclosure: Kaupr (kaupr.io) sponsors Kryptonytt and is one of our sources.

Saker frå Kaupr er merkte «Kaupr er sponsor» i samandraget.

## 6. E-postkanalen (påmelding på nettstaden) og flytting til Substack

- Skjema: nedst på kvar side + `/nyhetsbrev/` (nn), `/bm/nyhetsbrev/` (nb), `/en/nyhetsbrev/` (en); `/newsletter/` sender
  vidare dit. Med personvernmerknad. Av til `newsletter/config.json` har `enabled: true` og `endpoint` = Worker-adressa.
  Testbygg: `KRYPTONYTT_NEWSLETTER=1 NEWSLETTER_ENDPOINT=http://127.0.0.1:8789 KN_SITE_DIR=/tmp/x .venv/bin/python build.py`.
- Dobbel stadfesting: påmelding → stadfestingslenkje (gyldig 7 dagar) → `confirmed`. Ustadfesta rader blir sletta etter
  7 dagar. Verken IP-adresse eller nettlesarinfo blir lagra. CORS berre for https://jqrgen.github.io.
- Stadfestings-e-postar blir **ikkje sende** før ein leverandør er vald og `MAIL_PROVIDER` + `MAIL_SEND_ENABLED=1` er sette på
  Workeren. Berre Substack: hald skjemaet av, eller bruk det og importer stadfesta adresser:
  `.venv/bin/python tipworker/export_subscribers.py --site kryptonytt` (i Crypto Nordic-repoet) → CSV i `state/newsletter/`
  (modus 600, gitignored; kolonnen `email` først) → Substack › Subscribers › Import. Slett CSV-fila etter importen.

## 7. Sjekkliste for jQrgen (ingenting av dette er gjort)

- [ ] Opprett Substack-publikasjonen med di eiga innlogging; stadfest underdomenet (forslag: kryptonyttnorge) og vurder forvekslingsfaren med Finuntium (tidlegare kryptonytt.substack.com).
- [ ] Godkjenn namn, avsendarnamn, svaradresse, slagord, om-tekst, kategoriar og profilbilete.
- [ ] Lim inn velkomst-e-posten (nn eller nb); språk norsk; betalt abonnement av.
- [ ] Vel leverandør for stadfestings-e-post (Resend, Buttondown, Postmark via webhook, eller berre Substack-import) og avsendaradresse (krev eit domene du styrer, for SPF/DKIM).
- [ ] Gi ein Cloudflare API-token for å deployere Workeren (`tipworker/deploy.sh` i Crypto Nordic-repoet), og godkjenn så at skjemaet blir slått på.
- [ ] Etter første import: set `substack_url` i `newsletter/config.json`, så lenkjer nettstaden til Substack.
