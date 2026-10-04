#!/usr/bin/env python3
"""Kryptonytt Norge – henter feeds, filtrerer på norske kryptoord, dedupliserer og oppdaterer
data/news.json og køen queue/review.json.

FRÅ 4. OKT. 2026 ER DETTE IKKJE STANDARD NYHEITSINNHENTING. Norske saker kjem no frå Nordic Crypto
(tools/import_nordic_crypto.py, køyrd av ./fetch.sh). Denne fila er teken vare på som reserve:
  ./fetch.sh --legacy-fetch [--days N]   # gammal eiga innhenting (RSS + nyheitssøk)
  ./fetch.sh --add URL ...               # manuelt tillegg av éi sak (framleis i bruk)
  .venv/bin/python fetch.py --events-only  # berre arrangementssøket (kalender/«Tidlegare arrangement»)

  .venv/bin/python fetch.py            # vanlig daglig kjøring (ser 7 dager tilbake)
  .venv/bin/python fetch.py --days 30  # førstegangskjøring / tilbakeblikk

Nye saker får status "pending" og publiseres IKKE før redaktøren har skrevet en egen kort
oppsummering (feltet "summary") og satt status "published" (se README.md).
Ingress/teaser fra feeden lagres bare lokalt i state/teasers.json som arbeidsgrunnlag og
publiseres aldri. Artikkeltekst hentes aldri (vi respekterer betalingsmurer).
"""
import argparse, datetime as dt, hashlib, json, os, re, sys, time, urllib.parse, urllib.robotparser
import requests, feedparser
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)
NOW = dt.datetime.now(dt.timezone.utc)

def load(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError: return default
def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
    os.replace(tmp, path)

CFG = load(P("sources.json"), None)
UA = CFG["user_agent"]; DELAY = CFG.get("min_delay_seconds", 2)
LOG = None  # opna først ved første logglinje (tools/import_nordic_crypto.py importerer denne fila utan å lage tomme loggfiler)
def log(*a):
    global LOG
    if LOG is None: os.makedirs(P("logs"), exist_ok=True); LOG = open(P("logs", dt.datetime.now().strftime("fetch-%Y%m%d-%H%M%S.log")), "w", encoding="utf-8")
    s = " ".join(str(x) for x in a); print(s); LOG.write(s + "\n"); LOG.flush()

# ---------- høflig HTTP: robots.txt, rate limit per vert, ETag-cache ----------
_robots, _last = {}, {}
http_cache = load(P("state", "http_cache.json"), {})
def robots_ok(url):
    p = urllib.parse.urlparse(url); base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=15)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except Exception: rp.parse([])
        _robots[base] = rp
    return _robots[base].can_fetch(UA, url)
def get(url):
    host = urllib.parse.urlparse(url).netloc
    wait = DELAY - (time.time() - _last.get(host, 0))
    if wait > 0: time.sleep(wait)
    h = {"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"}
    c = http_cache.get(url, {})
    if c.get("etag"): h["If-None-Match"] = c["etag"]
    if c.get("lm"): h["If-Modified-Since"] = c["lm"]
    r = requests.get(url, headers=h, timeout=25); _last[host] = time.time()
    if r.status_code == 200:
        http_cache[url] = {"etag": r.headers.get("ETag"), "lm": r.headers.get("Last-Modified")}
    return r

# ---------- filtrering og klassifisering ----------
KW = [  # (regex, flags) – norske og internasjonale kryptoord
    (r"\bbitcoin\w*", re.I), (r"\bkrypto(?!graf)\w*", re.I), (r"\bcrypto\w*", re.I), (r"\bblokkjede\w*", re.I),
    (r"\bblockchain\w*", re.I), (r"\bNFT(?:-?\w*)?\b", 0), (r"\bstablecoin\w*", re.I), (r"\bMiCA\b", 0),
    (r"\bBare Bitcoin\b", re.I), (r"\bFiri\b", 0), (r"\bBitmynt\b", re.I), (r"\bNexa\b", 0), (r"\bethereum\b", re.I),
    (r"\bBTC\b", 0), (r"\bK33\b", 0), (r"\bNBX\b", 0), (r"\bsentralbankpenger\b", re.I), (r"\bweb3\b", re.I),
    (r"\btokeniser\w*", re.I), (r"\bsolana\b", re.I), (r"\bkryptoeiendel\w*", re.I), (r"\bCBDC\b", 0),
    (r"\bdigitale penger\b", re.I), (r"\bsatoshi\w*", re.I), (r"\bkryptovaluta\w*", re.I), (r"\bH100\b", 0),
]
KW = [(re.compile(r, f), r) for r, f in KW]
TOPICS = {
    "bitcoin": r"\bbitcoin|\bBTC\b|\bsatoshi|\butvinning|\bmining\b|\bminer",
    "blokkjede": r"\bblokkjede|\bblockchain|\bNFT|\btoken|\bweb3|\bethereum|\bsolana|\bNexa\b|\bsmart ?contract",
    "krypto": r"\bkrypto(?!graf)|\bcrypto|\bstablecoin|\bcoin\b",
    "regulering": r"finanstilsyn|\bMiCA\b|regulering|regelverk|\bskatt|forbud|\blov(?:en|forslag|endring)?\b|økokrim|hvitvask|sanksjon|\btilsyn|norges bank|skatteetaten|storting|departement|\bpoliti|\bdom(?:men|stol)?\b|\bsvindel|\bkonsesjon|\bCBDC|sentralbank",
    "selskaper": r"\bFiri\b|bare bitcoin|bitmynt|\bK33\b|\bNBX\b|\bH100\b|\bKaupr\b|\bNexa\b|selskap|\bbørs\b|kryptobørs|oppkjøp|emisjon|investor|gründer|\bASA\b|\bAS\b|omsetning|\bkunder\b",
}
TOPICS = {k: re.compile(v, re.I) for k, v in TOPICS.items()}
def matches(text, extra=()):
    hits = sorted({r for c, r in KW if c.search(text)} | {e for e in extra if e.lower() in text.lower()})
    return hits
def topics_of(text):
    return [k for k, c in TOPICS.items() if c.search(text)] or ["krypto"]

def clean(html):
    return re.sub(r"\s+", " ", BeautifulSoup(html or "", "lxml").get_text(" ")).strip()
TRACKING = re.compile(r"^(utm_.*|fbclid|gclid|gclsrc|dclid|msclkid|yclid|twclid|igshid|mc_cid|mc_eid|_hsenc|_hsmi|mkt_tok|ref|ref_src|ref_url|cmpid|ocid|ncid|xtor|s_cid|wt_mc|at_.*|spm|share|guccounter|guce_.*|__twitter_impression|cmp|campaign)$", re.I)
def norm_url(url):
    """Normalisert URL for duplikatsjekk: https, små bokstaver i vert, uten www./standardport, uten avsluttende /,
    uten sporingsparametre (utm_*, fbclid, gclid …), sortert spørring, uten fragment."""
    p = urllib.parse.urlparse(url.strip())
    host = (p.hostname or "").lower().removeprefix("www.")
    if p.port and p.port not in (80, 443): host += f":{p.port}"
    q = sorted((k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not TRACKING.match(k))
    return urllib.parse.urlunparse(("https", host, p.path.rstrip("/") or "/", "", urllib.parse.urlencode(q), ""))
def strip_tracking(url):
    p = urllib.parse.urlparse(url.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not TRACKING.match(k)]
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(q), fragment=""))
canon = norm_url
def _canon_v1(url):  # bare for stabile id-er (iid) på eksisterende saker; ikke for sammenligning
    p = urllib.parse.urlparse(url.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref"))]
    return urllib.parse.urlunparse((p.scheme.lower() or "https", p.netloc.lower().removeprefix("www."), p.path.rstrip("/") or "/", "", urllib.parse.urlencode(q), ""))
def norm_title(t): return re.sub(r"[^\wæøå]+", " ", t.lower()).strip()
def iid(url): return hashlib.sha1(_canon_v1(strip_tracking(url)).encode()).hexdigest()[:12]
def when(e):
    for k in ("published_parsed", "updated_parsed"):
        if e.get(k): return dt.datetime(*e[k][:6], tzinfo=dt.timezone.utc)
    return None

# ---------- kildekart (domene -> utsalg) ----------
SRC = {s["id"]: s for s in CFG["sources"]}
DOMAIN2OUT = {}
for s in CFG["sources"]:
    if s.get("type") == "bing": continue
    d = urllib.parse.urlparse(s["url"]).netloc.removeprefix("www.")
    DOMAIN2OUT.setdefault(d, s.get("outlet", s["id"]))
def outlet_for(url, fallback_name):
    d = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    for dom, out in DOMAIN2OUT.items():
        if d == dom or d.endswith("." + dom): return out, SRC[out]["name"] if out in SRC else fallback_name
    return d, fallback_name or d

# ---------- kandidat-entiteter til køen (aldri auto-publisert) ----------
KNOWN = ["Firi", "Bare Bitcoin", "Bitmynt", "K33", "NBX", "Norwegian Block Exchange", "Kaupr", "H100", "Nexa", "Bitcoin Unlimited",
 "Finanstilsynet", "Norges Bank", "Skatteetaten", "Økokrim", "Finansdepartementet", "Stortinget", "Kripos", "Forbrukerrådet",
 "Bitcoinpolitisk institutt", "Arcane Crypto", "Seetee", "Aker", "Kryptovault", "Bitfury", "Northern Data", "Green Mining",
 "COWI", "Statnett", "Nordic Blockchain Association", "Kryptoforeningen", "Wallet of Satoshi", "Barefoot Mining", "Coinbase",
 "Binance", "Kraken", "Revolut", "Nordnet", "DNB", "SpareBank 1", "Vipps", "Tether", "Circle", "Strategy", "BlackRock"]
ROLE = r"(?:daglig leder|administrerende direktør|adm\. ?dir\.?|toppsjef|sjef|gründer|medgründer|grunnlegger|styreleder|direktør|analytiker|sjefanalytiker|sentralbanksjef|visesentralbanksjef|finansminister|digitaliseringsminister|partner|investor|leder|seksjonssjef|avdelingsdirektør|talsperson|kommunikasjonssjef|fagdirektør|aktor|statsadvokat)"
NAME = r"[A-ZÆØÅ][a-zæøåéü]+(?:[- ][A-ZÆØÅ][a-zæøåéü\.]+){1,3}"
PAT = [re.compile(rf"(?P<role>{ROLE}) (?:i|for|hos|på|ved) (?P<org>[A-ZÆØÅ0-9][\w\.&-]*(?: [A-ZÆØÅ0-9][\w\.&-]*){{0,3}}),? (?P<name>{NAME})"),
       re.compile(rf"(?P<name>{NAME}),? (?:er )?(?P<role>{ROLE}) (?:i|for|hos|på|ved) (?P<org>[A-ZÆØÅ0-9][\w\.&-]*(?: [A-ZÆØÅ0-9][\w\.&-]*){{0,3}})"),
       re.compile(rf"(?P<org>[A-ZÆØÅ0-9][\w\.&-]*(?: [A-ZÆØÅ0-9][\w\.&-]*){{0,2}})-(?P<role>{ROLE}) (?P<name>{NAME})")]
def candidates(text):
    out = []
    for o in KNOWN:
        if re.search(rf"\b{re.escape(o)}\b", text): out.append({"kind": "organisasjon", "name": o})
    for p in PAT:
        for m in p.finditer(text):
            g = m.groupdict(); out.append({"kind": "person", "name": g["name"].strip(" ."), "role": g["role"], "org": g["org"].strip(" .,")})
    return out

EN_MONTHS = {m: i for i, m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"], 1)}
NO_MONTHS = {m: i for i, m in enumerate(["januar","februar","mars","april","mai","juni","juli","august","september","oktober","november","desember"], 1)}
def page_meta(url):
    """Henter bare offentlig metadata (tittel, ingress/description, dato) fra en side. Aldri artikkeltekst."""
    if not robots_ok(url): raise RuntimeError("robots.txt tillater ikke")
    r = get(url); r.raise_for_status(); soup = BeautifulSoup(r.text, "lxml")
    m = lambda **k: (soup.find("meta", attrs=k) or {}).get("content")
    title = m(property="og:title") or (soup.title.string if soup.title else "") or ""
    desc = m(property="og:description") or m(name="description") or ""
    date = None
    iso = m(property="article:published_time") or m(name="date") or m(name="DC.date")
    if iso:
        try: date = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError: date = None
    if not date:
        t = soup.get_text(" ", strip=True)
        x = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (20\d\d)", t)
        if x: date = dt.datetime(int(x[3]), EN_MONTHS[x[1]], int(x[2]), 12, tzinfo=dt.timezone.utc)
        else:
            x = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(20\d\d)\b", t) or None
            if x: date = dt.datetime(int(x[3]), int(x[2]), int(x[1]), 12, tzinfo=dt.timezone.utc)
    if date and date.tzinfo is None: date = date.replace(tzinfo=dt.timezone.utc)
    return clean(title), clean(desc), date

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--only", help="kommaseparerte kilde-id-er")
    ap.add_argument("--add", metavar="URL", help="legg til én sak manuelt (researcher): henter tittel/dato fra sidens metadata")
    ap.add_argument("--source-name", help="kildenavn for --add (ellers fra sources.json eller domenet)")
    ap.add_argument("--date", help="publiseringsdato for --add (YYYY-MM-DD) hvis siden ikke oppgir den")
    ap.add_argument("--title", help="tittel for --add hvis siden ikke oppgir den")
    ap.add_argument("--origin", help="intern merknad om hvor tipset kom fra for --add, f.eks. \"tips fra Nordic Crypto\" (vises aldri offentlig)")
    ap.add_argument("--no-events", action="store_true", help="hopp over arrangementsøket")
    ap.add_argument("--events-only", action="store_true", help="hent bare arrangementer (ingen nyheter); brukt av ./fetch.sh når nyhetene kommer fra Nordic Crypto"); a = ap.parse_args()
    if a.events_only: return
    cutoff = NOW - dt.timedelta(days=a.days)
    news = load(P("data", "news.json"), {"items": []})
    teasers = load(P("state", "teasers.json"), {})
    queue = load(P("queue", "review.json"), {"items_needing_summary": [], "candidate_entities": []})
    rejected = load(P("state", "rejected_candidates.json"), [])
    org = load(P("data", "orgchart.json"), {"entities": [], "relations": []})
    known_names = {e["name"].lower() for e in org["entities"]} | {n.lower() for n in rejected}
    by_url = {canon(i["url"]): i for i in news["items"]}
    by_title = {norm_title(i["title"]): i for i in news["items"]}
    status = load(P("state", "source_status.json"), {})
    new = []

    def add(url, title, teaser, published, src, outlet, outlet_name, extra=(), all_rel=False, origin=None):
        url = strip_tracking(url)
        text = f"{title}. {teaser}"
        hits = matches(text, extra)
        if not hits and not all_rel: return
        if not published or published < cutoff: return
        cu = canon(url)
        if cu in by_url or norm_title(title) in by_title:
            ex = by_url.get(cu) or by_title.get(norm_title(title))
            if origin and not ex.get("origin"): ex["origin"] = origin
            if src not in ex.setdefault("seen_via", []): ex["seen_via"].append(src)
            return
        it = {"id": iid(url), "url": url, "title": title, "source": outlet, "source_name": outlet_name, "via": src,
              "seen_via": [src], "published": published.isoformat(), "fetched": NOW.isoformat(timespec="seconds"),
              "topics": topics_of(text), "matched": hits, "paywall": bool(SRC.get(outlet, {}).get("paywall", False)),
              "status": "pending", "summary": None}
        if origin: it["origin"] = origin  # intern merknad (f.eks. «tips fra Nordic Crypto»), vises aldri på nettstedet
        news["items"].append(it); by_url[cu] = it; by_title[norm_title(title)] = it
        teasers[it["id"]] = teaser[:600]; new.append(it)

    if a.add and norm_url(a.add) in by_url:  # duplikat (normalisert URL): ikke hent siden på nytt
        ex = by_url[norm_url(a.add)]
        if a.origin and not ex.get("origin"): ex["origin"] = a.origin
        log(f"FINNES ALLEREDE: {ex['title']} ({ex.get('status')})"); a.add = None; a.only = "__none__"
    if a.add:
        title, desc, date = page_meta(a.add)
        if a.title: title = a.title
        if a.date: date = dt.datetime.fromisoformat(a.date).replace(hour=12, tzinfo=dt.timezone.utc)
        if not date: sys.exit("fant ingen dato på siden; bruk --date YYYY-MM-DD")
        out, oname = outlet_for(a.add, a.source_name or urllib.parse.urlparse(a.add).netloc.removeprefix("www."))
        if a.source_name: oname = a.source_name
        before = len(new)
        add(a.add, title, desc, date, "manuell", out, oname, all_rel=True, origin=a.origin)
        log(("LAGT TIL: " if len(new) > before else "FINNES ALLEREDE/UTENFOR PERIODEN (--days): ") + f"{title} ({date.date()}, {oname})")
        a.only = "__none__"
    seen_html = load(P("state", "html_seen.json"), {})
    for s in CFG["sources"]:
        if not s.get("enabled") or not s.get("feed"): continue
        if a.only and s["id"] not in a.only.split(","): continue
        if s["type"] == "html":
            n_ok = 0; err = None; links = []
            try:
                if robots_ok(s["feed"]):
                    r = get(s["feed"]); r.raise_for_status(); n_ok = 1
                    soup = BeautifulSoup(r.text, "lxml")
                    links = sorted({urllib.parse.urljoin(s["feed"], x["href"]) for x in soup.find_all("a", href=True) if re.search(s["link_pattern"], x["href"])})
                else: err = "robots.txt tillater ikke"
                for u in links[: s.get("max_new_per_run", 40)]:
                    if u in seen_html: continue
                    t, d, date = page_meta(u)
                    seen_html[u] = {"title": t, "date": date.isoformat() if date else None}
                    add(u, t, d, date, s["id"], s.get("outlet", s["id"]), s["name"], all_rel=s.get("all_relevant", False))
            except Exception as ex: err = f"{type(ex).__name__}: {ex}"[:200]; log("ERR", s["id"], err)
            status[s["id"]] = {"checked": NOW.isoformat(timespec="seconds"), "ok": n_ok > 0, "requests": 1 + len(links), "ok_requests": n_ok, "entries": len(links), "error": err}
            log(f"{s['id']:<22} html links={len(links)} err={err}"); continue
        if a.only and s["id"] not in a.only.split(","): continue
        urls = []
        if s["type"] == "bing":
            for q in s.get("queries", []):
                urls.append(s["feed"].format(q=urllib.parse.quote(q)))
            for site in s.get("sites", []):
                for t in s.get("site_terms", []):
                    urls.append(s["feed"].format(q=urllib.parse.quote(f"{t} site:{site}")))
        else: urls = [s["feed"]]
        n_ok = n_items = 0; err = None
        for u in urls:
            if not robots_ok(u): err = "robots.txt tillater ikke"; log("SKIP robots", s["id"], u); continue
            try:
                r = get(u)
                if r.status_code == 304: n_ok += 1; continue
                if r.status_code != 200: err = f"HTTP {r.status_code}"; continue
                f = feedparser.parse(r.content); n_ok += 1; n_items += len(f.entries)
                for e in f.entries:
                    link = e.get("link") or ""
                    title = clean(e.get("title"))
                    teaser = clean(e.get("summary") or e.get("description") or "")
                    if s["type"] == "bing":
                        qs = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                        link = (qs.get("url") or [link])[0]
                        if not urllib.parse.urlparse(link).netloc.endswith(s.get("allowed_tld", ".no")): continue
                        out, oname = outlet_for(link, (e.get("news_source") or "").strip())
                        add(link, title, teaser, when(e), s["id"], out, oname)
                    else:
                        out = s.get("outlet", s["id"]); oname = SRC.get(out, s)["name"]
                        add(link, title, teaser, when(e), s["id"], out, oname, s.get("match_extra", ()), s["type"] == "rss-all")
            except Exception as ex:
                err = f"{type(ex).__name__}: {ex}"[:200]; log("ERR", s["id"], u, err)
        status[s["id"]] = {"checked": NOW.isoformat(timespec="seconds"), "ok": n_ok > 0, "requests": len(urls),
                           "ok_requests": n_ok, "entries": n_items, "error": err}
        log(f"{s['id']:<22} ok={n_ok}/{len(urls)} entries={n_items} err={err}")

    # kø: saker uten redaksjonell oppsummering + kandidat-entiteter
    pend = {q["id"] for q in queue["items_needing_summary"]}
    for it in news["items"]:
        if it["status"] == "pending" and it["id"] not in pend:
            queue["items_needing_summary"].append({"id": it["id"], "title": it["title"], "source": it["source_name"],
                "url": it["url"], "published": it["published"], "teaser_local_only": teasers.get(it["id"], ""),
                **({"origin": it["origin"]} if it.get("origin") else {})})
    for q_ in queue["items_needing_summary"]:  # behold/oppdater origin ved hver ny bygging av køen
        src_it = next((i for i in news["items"] if i["id"] == q_["id"]), None)
        if src_it and src_it.get("origin"): q_["origin"] = src_it["origin"]
    queue["items_needing_summary"] = [q for q in queue["items_needing_summary"]
        if any(i["id"] == q["id"] and i["status"] == "pending" for i in news["items"])]
    seen_c = {(c["name"].lower(), c.get("item_id")) for c in queue["candidate_entities"]}
    for it in new:
        for c in candidates(f"{it['title']}. {teasers.get(it['id'], '')}"):
            if c["name"].lower() in known_names or (c["name"].lower(), it["id"]) in seen_c: continue
            c.update({"item_id": it["id"], "url": it["url"], "source": it["source_name"], "status": "new"})
            queue["candidate_entities"].append(c); seen_c.add((c["name"].lower(), it["id"]))
    queue["updated"] = NOW.isoformat(timespec="seconds")
    queue["_how_to"] = ("Redaktør: for hver sak i items_needing_summary, skriv 1–2 egne setninger i data/news.json "
        "(felt summary, aldri kopiert tekst) og sett status=published, eller status=rejected hvis saken ikke handler om norsk krypto. "
        "Kandidat-entiteter: legg bekreftede inn i data/orgchart.json med kilde-lenke, og sett status=accepted/rejected her. "
        "Kjør deretter ./publish.sh.")
    news["items"].sort(key=lambda i: i["published"], reverse=True); news["updated"] = NOW.isoformat(timespec="seconds")
    save(P("data", "news.json"), news); save(P("state", "teasers.json"), teasers); save(P("queue", "review.json"), queue)
    save(P("state", "source_status.json"), status); save(P("state", "http_cache.json"), http_cache); save(P("state", "html_seen.json"), seen_html)
    log(f"FERDIG: {len(new)} nye saker, {len(news['items'])} totalt, "
        f"{len(queue['items_needing_summary'])} venter på oppsummering, "
        f"{sum(1 for c in queue['candidate_entities'] if c['status']=='new')} nye kandidat-entiteter i queue/review.json")

if __name__ == "__main__":
    main()
    if "--add" not in sys.argv and "--no-events" not in sys.argv:  # arrangementer søkes ved hver henting
        import events
        events.run(get, robots_ok, lambda t: bool(matches(t)), log, CFG)
