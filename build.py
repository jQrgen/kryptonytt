#!/usr/bin/env python3
"""Bygger den statiske siden i site/ fra data/news.json, data/orgchart.json og sources.json.
Bare saker med status=published og egen oppsummering, og entiteter/relasjoner med status=published
og minst én kildelenke, kommer med. Ingen sporing, ingen tredjepartsskript, ingen eksterne fonter."""
import json, os, re, shutil, subprocess, html, datetime as dt
ROOT = os.path.dirname(os.path.abspath(__file__)); P = lambda *a: os.path.join(ROOT, *a)
BASE = "https://jqrgen.github.io/kryptonytt/"
SITE = P("site")
def load(p, d=None):
    try: return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError: return d
E = lambda s: html.escape(str(s if s is not None else ""), quote=True)
def snippets(url, title):
    return json.loads(subprocess.check_output(["node", P("tools", "snippets.js"), url, title]))
MONTHS = ["jan.", "feb.", "mars", "april", "mai", "juni", "juli", "aug.", "sep.", "okt.", "nov.", "des."]
MORGEN = "Nyheter oppdateres daglig av kunstig intelligens"

def nodate(iso):
    d = dt.datetime.fromisoformat(iso).astimezone(dt.timezone(dt.timedelta(hours=2)))
    return f"{d.day}. {MONTHS[d.month-1]} {d.year}"

CSS = """
:root{--ink:#111;--muted:#4B5563;--line:#d1d5db;--paper:#fff;--band:#111;--band-ink:#fff;--accent:#b45309;--soft:#f6f6f4;--pub:#1d4ed8;--priv:#047857}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--paper)}
a{color:inherit}a:hover{text-decoration-thickness:2px}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px}
header.top{border-bottom:3px solid var(--ink)}
header.top .wrap{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 22px;padding-top:14px;padding-bottom:10px}
.brand{font-weight:800;font-size:22px;letter-spacing:-.01em;text-decoration:none}.brand span{color:var(--accent)}
nav.main{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:15px}
nav.main a{text-decoration:none;padding:2px 0;border-bottom:2px solid transparent}nav.main a[aria-current]{border-color:var(--accent);font-weight:600}
h1{font-size:28px;line-height:1.2;margin:22px 0 4px}h2{font-size:20px;margin:28px 0 8px}
.lead{color:var(--muted);margin:4px 0 10px;max-width:70ch}
.filters{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:14px 0;padding:10px 12px;background:var(--soft);border:1px solid var(--line)}
.filters label{font-size:14px;color:var(--muted)}
select,input[type=search]{font:inherit;font-size:15px;padding:5px 8px;border:1px solid var(--ink);background:#fff;border-radius:0;max-width:100%}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:inherit;font-size:13.5px;padding:3px 10px;border:1px solid var(--ink);background:#fff;cursor:pointer}
.chip[aria-pressed=true]{background:var(--ink);color:#fff}
ol.news{list-style:none;margin:0;padding:0}
ol.news li{padding:14px 0;border-bottom:1px solid var(--line)}
ol.news h3{font-size:18px;line-height:1.3;margin:0 0 4px}ol.news h3 a{text-decoration:none}ol.news h3 a:hover{text-decoration:underline}
.meta{font-size:13.5px;color:var(--muted)}.meta b{color:var(--ink);font-weight:600}
.tag{display:inline-block;font-size:12px;padding:0 6px;border:1px solid var(--line);margin-left:4px;color:var(--muted)}
.sum{margin:6px 0 0;max-width:75ch}
.pw{font-size:12px;color:var(--accent)}
.morgen{font-size:13px;color:var(--muted);margin:6px 0}
.calgrid{display:none}@media(min-width:760px){.calgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;margin:16px 0}}
table.cal{border-collapse:collapse;width:100%;table-layout:fixed;font-size:13px}table.cal caption{text-align:left;font-weight:600;padding:4px 0}
table.cal th{font-weight:500;color:var(--muted);padding:2px}table.cal td{border:1px solid var(--line);vertical-align:top;height:58px;padding:2px 4px;overflow:hidden}
table.cal td.out{opacity:.35}table.cal td.today .d{background:var(--accent);color:#fff;padding:0 4px}table.cal td.has{background:color-mix(in srgb,var(--accent) 8%,transparent)}
table.cal td a{display:block;font-size:12px;line-height:1.2;margin-top:2px}ol.past{opacity:.7}
.empty{padding:20px;color:var(--muted)}
footer{margin-top:40px;border-top:1px solid var(--line);padding:18px 0 30px;font-size:13.5px;color:var(--muted)}
.notice{border-left:4px solid var(--accent);background:var(--soft);padding:8px 12px;font-size:14px;margin:12px 0}
/* org chart */
.seg{display:inline-flex;border:1px solid var(--ink)}.seg button{font:inherit;font-size:14px;padding:5px 12px;border:0;background:#fff;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--ink);color:#fff}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:12px}
.cols.only-privat{grid-template-columns:1fr}.cols.only-offentlig{grid-template-columns:1fr}
.cols.only-privat .col-offentlig,.cols.only-offentlig .col-privat{display:none}
@media (max-width:760px){.cols{grid-template-columns:1fr}}
.col h2{margin:0 0 8px;padding:6px 10px;color:#fff;font-size:17px}
.col-privat h2{background:var(--priv)}.col-offentlig h2{background:var(--pub)}
.grp{margin:0 0 14px}.grp h3{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:10px 0 6px}
.card{border:1px solid var(--line);background:#fff;padding:8px 10px;margin:0 0 8px;cursor:pointer;text-align:left;width:100%;font:inherit;display:block}
.card:hover,.card:focus-visible{border-color:var(--ink);outline:none}
.card.hl{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent)}.card.dim{opacity:.35}
.card .nm{font-weight:700}.card .ds{font-size:13.5px;color:var(--muted)}
.people{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.person{display:flex;align-items:center;gap:6px;font-size:13px;border:1px solid var(--line);padding:3px 8px 3px 3px;background:var(--soft);cursor:pointer;font-family:inherit}
.person.hl{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent)}
.av{width:34px;height:34px;border-radius:50%;object-fit:cover;flex:none;display:inline-flex;align-items:center;justify-content:center;background:#e5e7eb;color:#374151;font-weight:700;font-size:13px}
.av.big{width:96px;height:96px;font-size:28px}
.xl{font-size:11.5px;padding:0 5px;margin-left:4px;border:1px solid}.xl.pub{color:var(--pub)}.xl.priv{color:var(--priv)}
#detail{position:sticky;bottom:0;background:#fff;border:2px solid var(--ink);padding:12px 14px;margin-top:14px;max-height:60vh;overflow:auto}
#detail[hidden]{display:none}#detail h3{margin:0 0 4px;font-size:19px}#detail .close{float:right;font:inherit;border:1px solid var(--ink);background:#fff;cursor:pointer}
#detail ul{padding-left:18px;margin:6px 0}#detail .row{display:flex;gap:14px;align-items:flex-start}
.credit{font-size:12px;color:var(--muted)}
table.list{width:100%;border-collapse:collapse;font-size:14.5px}table.list th,table.list td{border-bottom:1px solid var(--line);padding:6px 6px;text-align:left;vertical-align:top}
table.list th{font-size:13px;color:var(--muted)}
.ok{color:#047857;font-weight:600}.bad{color:#b91c1c;font-weight:600}
.prose{max-width:72ch}
"""

def page(slug, title, nav, body, desc, extra_script=""):
    url = BASE + (slug + "/" if slug else "")
    s = snippets(url, f"{title} – Kryptonytt Norge" if slug else "Kryptonytt Norge – norske kryptonyheter")
    navs = [("", "Nyheter"), ("organisasjonskart", "Hvem er hvem"), ("kalender", "Kalender"), ("kilder", "Kilder"), ("om", "Om")]
    rel = "../" if slug else "./"
    nav_html = "".join(f'<a href="{rel}{n + "/" if n else ""}"{" aria-current=page" if n == nav else ""}>{E(t)}</a>' for n, t in navs)
    doc = f"""<!doctype html>
<html lang="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}{" – Kryptonytt Norge" if slug else ""}</title>
<meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}"><meta property="og:type" content="website"><meta property="og:locale" content="nb_NO">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%23b45309'/%3E%3Ctext x='8' y='12.5' font-size='12' text-anchor='middle' fill='white' font-family='sans-serif' font-weight='bold'%3EK%3C/text%3E%3C/svg%3E">
<style>{CSS}{s['css']}</style></head>
<body><header class="top"><div class="wrap"><a class="brand" href="{rel}">Krypto<span>nytt</span> Norge</a><nav class="main" aria-label="Hovedmeny">{nav_html}</nav></div></header>
<main class="wrap">
{body}
{s['top']}
</main>
<footer><div class="wrap">Kryptonytt Norge drives av Jørgen S. Notland (jQrgen), Oslo, med hjelp av kunstig intelligens. Ansvarlig redaktør: «Kryptonytt redaktør» (en bot basert på kunstig intelligens), med jQrgen som ansvarlig person. Ingen investeringsråd. Ingen sporing eller informasjonskapsler. <a href="{rel}om/">Om, rettelser og fjerning</a>.<p class="morgen">{E(MORGEN)}</p></div></footer>
{s['script']}{extra_script}
</body></html>"""
    d = os.path.join(SITE, slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(doc)

TOPIC_LABEL = {"bitcoin": "Bitcoin", "blokkjede": "Blokkjede", "krypto": "Krypto", "regulering": "Regulering", "selskaper": "Selskaper"}

def build():
    subprocess.run([os.sys.executable, P("tools", "import_industrikart.py")], check=True)
    subprocess.run([os.sys.executable, P("tools", "apply_approvals.py")], check=True)
    news = load(P("data", "news.json"), {"items": []}); org = load(P("data", "orgchart.json"), {"entities": [], "relations": []})
    cfg = load(P("sources.json")); status = load(P("state", "source_status.json"), {})
    if os.path.exists(SITE): shutil.rmtree(SITE)
    os.makedirs(os.path.join(SITE, "data"))
    items = [i for i in news["items"] if i.get("status") == "published" and (i.get("summary") or "").strip()]
    items.sort(key=lambda i: i["published"], reverse=True)
    pub_items = [{k: i[k] for k in ("id", "url", "title", "source", "source_name", "published", "topics", "summary", "paywall", "links") if k in i} for i in items]
    ents = [e for e in org["entities"] if e.get("status") == "published" and e.get("sources")]
    eids = {e["id"] for e in ents}
    rels = [r for r in org["relations"] if r.get("status") == "published" and r.get("sources") and r["from"] in eids and r["to"] in eids]
    json.dump({"updated": news.get("updated"), "items": pub_items}, open(os.path.join(SITE, "data", "news.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pub_org = {"updated": org.get("updated"), "entities": ents, "relations": rels}
    summ = org.get("summary") or []
    json.dump(pub_org, open(os.path.join(SITE, "data", "orgchart.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # bilder (bare de som brukes og har lisens)
    for e in ents:
        im = e.get("image")
        if im and im.get("file") and im.get("license"):
            src = P(im["file"]); dst = os.path.join(SITE, im["file"]); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(src, dst)

    # ---- Nyheter ----
    srcs = sorted({(i["source"], i["source_name"]) for i in items}, key=lambda x: x[1].lower())
    lis = []
    for i in items:
        tags = "".join(f'<span class="tag">{E(TOPIC_LABEL.get(t, t))}</span>' for t in i["topics"])
        pw = ' · <span class="pw">kan kreve abonnement</span>' if i.get("paywall") else ""
        lis.append(f'<li data-src="{E(i["source"])}" data-topics="{E(" ".join(i["topics"]))}"><h3><a href="{E(i["url"])}" rel="noopener" target="_blank">{E(i["title"])}</a></h3>'
                   f'<div class="meta"><b>{E(i["source_name"])}</b> · <time datetime="{E(i["published"])}">{nodate(i["published"])}</time>{pw} {tags}</div>'
                   f'<p class="sum">{E(i["summary"])}</p>' + ("".join(f'<div class="meta">↳ <a href="{E(l["url"])}" rel="noopener" target="_blank">{E(l["label"])}</a></div>' for l in i.get("links", []))) + '</li>')
    opts = "".join(f'<option value="{E(k)}">{E(n)}</option>' for k, n in srcs)
    chips = "".join(f'<button type="button" class="chip" data-t="{k}" aria-pressed="false">{v}</button>' for k, v in TOPIC_LABEL.items())
    upd = nodate(news["updated"]) if news.get("updated") else ""
    body = f"""<h1>Norske nyheter om bitcoin, blokkjede og krypto</h1>
<p class="meta"><a href="skjerm/">Skjermmodus for kontorskjerm (fullskjerm, høykant eller liggende) →</a></p>
<p class="lead">Lenker til norske saker fra aviser, myndigheter, blogger og podkaster, med en kort oppsummering skrevet av redaksjonen. Les hele saken hos kilden. Sist oppdatert {upd}. {len(items)} saker.</p>
<div class="filters" role="group" aria-label="Filter"><label for="fsrc">Kilde</label><select id="fsrc"><option value="">Alle kilder</option>{opts}</select>
<label>Tema</label><div class="chips">{chips}</div><span id="count" class="meta" aria-live="polite"></span></div>
<p class="morgen">{E(MORGEN)}</p>
<ol class="news" id="news">{''.join(lis) or '<li class="empty">Ingen publiserte saker ennå.</li>'}</ol>
<p class="notice">Oppsummeringene er våre egne, skrevet ut fra tittel og ingress. Vi gjengir ikke artikkeltekst. Saker merket «kan kreve abonnement» ligger hos en avis med betalingsmur. Ingenting her er investeringsråd.</p>"""
    js = """<script>
(function(){var sel=document.getElementById('fsrc'),chips=[].slice.call(document.querySelectorAll('.chip')),lis=[].slice.call(document.querySelectorAll('#news li[data-src]')),cnt=document.getElementById('count');
function q(){var p=new URLSearchParams(location.hash.slice(1));return p}
function apply(push){var s=sel.value,t=chips.filter(function(c){return c.getAttribute('aria-pressed')==='true'}).map(function(c){return c.dataset.t}),n=0;
lis.forEach(function(li){var ok=(!s||li.dataset.src===s)&&(!t.length||t.some(function(x){return (' '+li.dataset.topics+' ').indexOf(' '+x+' ')>=0}));li.hidden=!ok;if(ok)n++});
cnt.textContent=n+' saker';if(push){var p=new URLSearchParams();if(s)p.set('kilde',s);if(t.length)p.set('tema',t.join(','));history.replaceState(null,'',p.toString()?'#'+p:location.pathname)}}
var p=q();if(p.get('kilde'))sel.value=p.get('kilde');(p.get('tema')||'').split(',').forEach(function(x){chips.forEach(function(c){if(c.dataset.t===x)c.setAttribute('aria-pressed','true')})});
sel.addEventListener('change',function(){apply(1)});chips.forEach(function(c){c.addEventListener('click',function(){c.setAttribute('aria-pressed',c.getAttribute('aria-pressed')==='true'?'false':'true');apply(1)})});apply(0)})();
</script>"""
    page("", "Kryptonytt Norge – norske nyheter om bitcoin, blokkjede og krypto", "", body,
         "Norske nyheter om bitcoin, blokkjede og kryptovaluta samlet på ett sted, med kilder og et organisasjonskart over hvem er hvem i norsk krypto.", js)

    # ---- Organisasjonskart ----
    body = f"""<h1>Hvem er hvem i norsk krypto</h1>
<p class="lead">Selskaper, organisasjoner, myndigheter og personer i offentlige yrkesroller, slik de er omtalt i nyhetene vi lenker til. Hver oppføring og hver kobling har lenke til kilden. Klikk på et kort for detaljer og koblinger på tvers av privat og offentlig sektor.</p>
{('<details class="notice" open><summary><b>Oversikt: slik henger norsk kryptoregulering og -bransje sammen</b> (per ' + E(org.get("updated") or "") + ')</summary>' + "".join(f"<p>{E(x)}</p>" for x in summ) + '</details>') if summ else ''}
{('<details class="notice"><summary>Forbehold</summary><ul>' + "".join(f"<li>{E(x)}</li>" for x in org.get("caveats", [])) + '</ul></details>') if org.get("caveats") else ''}
<div class="filters"><div class="seg" role="group" aria-label="Vis sektor"><button type="button" data-v="begge" aria-pressed="true">Begge</button><button type="button" data-v="privat" aria-pressed="false">Privat sektor</button><button type="button" data-v="offentlig" aria-pressed="false">Offentlig sektor</button></div>
<label for="osearch">Søk</label><input type="search" id="osearch" placeholder="Navn, rolle, organisasjon"></div>
<div id="chart" class="cols"><noscript>Kartet krever JavaScript; se listen under.</noscript></div>
<section id="detail" hidden aria-live="polite"></section>
<h2 id="liste">Søkbar liste</h2>
<table class="list" id="olist"><thead><tr><th>Navn</th><th>Type</th><th>Sektor</th><th>Rolle / beskrivelse</th><th>Kilder</th></tr></thead><tbody></tbody></table>
<p class="notice">Vi tar bare med det som står i kildene: navn, offentlig yrkesrolle og organisasjon. Ingen private opplysninger. Bilder vises bare når de har fri lisens (Wikimedia Commons) eller er pressebilder som eksplisitt kan brukes; ellers viser vi initialer og lenker til bildet hos kilden. Feil? Se <a href="../om/#rettelser">rettelser og fjerning</a>.</p>
<script id="orgdata" type="application/json">{json.dumps(pub_org, ensure_ascii=False).replace("</", "<\\/")}</script>"""
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    page("organisasjonskart", "Hvem er hvem i norsk krypto", "organisasjonskart", body,
         "Organisasjonskart over norsk krypto: selskaper, organisasjoner, myndigheter og personer i offentlige roller, med kildelenker.",
         "<script>" + open(P("tools", "orgchart.js"), encoding="utf-8").read() + "</script>")

    # ---- Kilder ----
    rows = []
    for s in cfg["sources"]:
        st = status.get(s["id"], {})
        if s["type"] == "search": cls, lab = "ok", "via nyhetssøk"
        elif s.get("enabled") and st.get("ok", True): cls, lab = "ok", "overvåkes"
        elif s.get("search_fallback"): cls, lab = "bad", "RSS virker ikke (via nyhetssøk)"
        else: cls, lab = "bad", "virker ikke"
        feed = f'<a href="{E(s["feed"])}" rel="noopener">feed</a>' if s.get("feed") and "{q}" not in s["feed"] else ("søk" if s.get("feed") else "–")
        rows.append(f'<tr><td><a href="{E(s["url"])}" rel="noopener" target="_blank">{E(s["name"])}</a></td><td>{E(s["kind"])}</td><td>{feed}</td>'
                    f'<td class="{cls}">{lab}</td><td>{E(s.get("status", ""))}</td></tr>')
    bs = next((s for s in cfg["sources"] if s["type"] == "bing"), {})
    qs = bs.get("queries", []) + [f"«{t}» på {len(bs.get('sites', []))} norske nettsteder" for t in bs.get("site_terms", [])]
    body = f"""<h1>Kilder vi følger</h1>
<p class="lead">Aviser, myndigheter, blogger og podkaster vi henter overskrifter fra. Vi leser RSS-feeder og et nyhetssøk, følger robots.txt, identifiserer oss med en egen brukeragent og holder minst {cfg.get("min_delay_seconds", 2)} sekunder mellom forespørsler til samme nettsted. Vi henter aldri artikkeltekst bak betalingsmur.</p>
<table class="list"><thead><tr><th>Kilde</th><th>Type</th><th>Feed</th><th>Status</th><th>Merknad</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Søkeord i nyhetssøket</h2><p class="prose">{E(", ".join(qs))}. Fra søket tar vi bare med saker fra norske domener (.no), og lenken går alltid direkte til originalsaken.</p>
<h2>Nøkkelord</h2><p class="prose">En sak tas med når tittel eller ingress nevner for eksempel bitcoin, krypto, kryptovaluta, blokkjede, blockchain, NFT, stablecoin, MiCA, sentralbankpenger, Bare Bitcoin, Firi, Bitmynt, K33, NBX eller Nexa. Redaksjonen går gjennom alle treff før de publiseres.</p>
<p class="meta">Mangler en kilde? Foreslå den som en sak på <a href="https://github.com/jQrgen/kryptonytt/issues" rel="noopener">GitHub</a>.</p>"""
    page("kilder", "Kilder", "kilder", body, "Norske aviser, myndigheter, blogger og podkaster som Kryptonytt Norge følger.")

    # ---- Kalender ----
    build_calendar(cfg, status)
    # ---- Om ----
    body = open(P("templates", "om.html"), encoding="utf-8").read()
    page("om", "Om Kryptonytt Norge", "om", body, "Om Kryptonytt Norge: hvem som står bak, redaksjonell policy, rettelser og fjerning.")
    # ---- Skjermmodus ----
    os.makedirs(os.path.join(SITE, "skjerm"), exist_ok=True)
    open(os.path.join(SITE, "skjerm", "index.html"), "w", encoding="utf-8").write(open(P("templates", "skjerm.html"), encoding="utf-8").read().replace("__BASE__", BASE))
    active = sorted({s["name"].split(" (")[0] for s in cfg["sources"] if s.get("enabled") and s["type"] not in ("bing",) and (s["type"] == "search" or status.get(s["id"], {}).get("ok", True))})
    json.dump({"active": active}, open(os.path.join(SITE, "data", "sources.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(SITE, "robots.txt"), "w").write("User-agent: *\nAllow: /\n")
    print(f"build: {len(items)} saker, {len(ents)} entiteter ({sum(e['type']=='person' for e in ents)} personer), {len(rels)} relasjoner -> {SITE}")

MND = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"]
UKEDAG = ["man", "tir", "ons", "tor", "fre", "lør", "søn"]

def events_for_site():
    """data/events.json + redaktørens valg i queue/approved.json -> events (approve/reject/notes/sponsored/paid)."""
    import datetime as dt
    from zoneinfo import ZoneInfo
    ev = load(P("data", "events.json"), {"events": []}); ap = (load(P("queue", "approved.json"), {}) or {}).get("events", {})
    now = dt.datetime.now(ZoneInfo("Europe/Oslo")); out = []
    for e in ev["events"]:
        e = dict(e)
        if e["id"] in ap.get("reject", []): continue
        if e["id"] in ap.get("approve", []): e["status"] = "published"
        if e["status"] != "published": continue
        if not (e.get("place") or e.get("online")) or not e.get("organiser") or not e.get("start"): continue  # regel: dato, sted og arrangør
        e["note"] = ap.get("notes", {}).get(e["id"])
        if e["id"] in ap.get("sponsored", []): e["sponsored"] = True
        if e["id"] in ap.get("paid", {}): e["paid"] = ap["paid"][e["id"]]
        end = dt.datetime.fromisoformat(e.get("end") or e["start"])
        e["past"] = end < now
        out.append({k: e.get(k) for k in ("id", "title", "start", "end", "place", "city", "online", "organiser", "url", "source", "paid", "sponsored", "note", "past")})
    return sorted(out, key=lambda e: e["start"]), now

def build_calendar(cfg, status):
    import calendar, datetime as dt
    evs, now = events_for_site()
    json.dump({"events": [e for e in evs if not e["past"]]}, open(os.path.join(SITE, "data", "events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    up = [e for e in evs if not e["past"]]; past = [e for e in evs if e["past"]][-10:][::-1]
    def when(e):
        a = dt.datetime.fromisoformat(e["start"]); b = dt.datetime.fromisoformat(e["end"]) if e.get("end") else None
        t = f'{UKEDAG[a.weekday()]} {a.day}. {MND[a.month-1]} {a.year} kl. {a:%H.%M}'
        return t + (f'–{b:%H.%M}' if b and b.date() == a.date() else (f' – {b.day}. {MND[b.month-1]}' if b else ""))
    def badges(e):
        b = []
        if e.get("paid"): b.append('<span class="tag pw">Betalt</span>')
        elif e.get("paid") is False: b.append('<span class="tag">Gratis</span>')
        if e.get("sponsored"): b.append('<span class="tag pw">Sponset</span>')
        if e.get("online"): b.append('<span class="tag">Digitalt</span>')
        return " ".join(b)
    def li(e):
        return (f'<li id="e-{E(e["id"])}"><h3><a href="{E(e["url"])}" rel="noopener" target="_blank">{E(e["title"])}</a></h3>'
                f'<div class="meta"><time datetime="{E(e["start"])}"><b>{E(when(e))}</b></time> · {E(e.get("place") or "Digitalt")} {badges(e)}</div>'
                f'<div class="meta">Arrangør: {E(e["organiser"])} · Kilde: <a href="{E(e["url"])}" rel="noopener" target="_blank">{E(e["source"])}</a></div>'
                + (f'<p class="sum"><b>Merk:</b> {E(e["note"])}</p>' if e.get("note") else "") + '</li>')
    # månedsrutenett for denne og neste måneder som har arrangementer
    months = sorted({(now.year, now.month)} | {(int(e["start"][:4]), int(e["start"][5:7])) for e in up})
    grids = []
    for y, m in months:
        cells = []
        for wk in calendar.Calendar(0).monthdatescalendar(y, m):
            row = []
            for d in wk:
                de = [e for e in up if e["start"][:10] == d.isoformat()]
                cls = " ".join(c for c in ["out" if d.month != m else "", "today" if d == now.date() else "", "has" if de else ""] if c)
                row.append(f'<td class="{cls}"><span class="d">{d.day}</span>' + "".join(f'<a href="#e-{E(e["id"])}">{E(e["title"])}</a>' for e in de) + '</td>')
            cells.append("<tr>" + "".join(row) + "</tr>")
        grids.append(f'<table class="cal"><caption>{MND[m-1].capitalize()} {y}</caption><thead><tr>{"".join(f"<th>{d}</th>" for d in UKEDAG)}</tr></thead><tbody>{"".join(cells)}</tbody></table>')
    esrc = "".join(f'<li><a href="{E(s["url"])}" rel="noopener" target="_blank">{E(s["name"])}</a> – {E(s.get("status", ""))}</li>' for s in cfg.get("event_sources", []) if s.get("enabled"))
    body = f"""<h1>Kalender: krypto, bitcoin og blokkjede i Norge</h1>
<p class="lead">Kommende arrangementer, møter og foredrag. Vi tar bare med arrangementer der arrangørens egen side eller en offentlig oppføring viser dato, sted og arrangør, og som faktisk handler om krypto, bitcoin eller blokkjede. Betalte og sponsede arrangementer er merket. Sjekk alltid detaljene hos arrangøren.</p>
<div class="calgrid">{''.join(grids)}</div>
<h2>Kommende</h2><ol class="news">{''.join(li(e) for e in up) or '<li class="empty">Ingen kommende arrangementer registrert.</li>'}</ol>
{('<h2>Tidligere</h2><ol class="news past">' + ''.join(li(e) for e in past) + '</ol>') if past else ''}
<h2>Hvor vi finner arrangementer</h2><ul class="prose">{esrc}</ul>
<p class="meta">Arrangerer du noe om krypto i Norge? Send lenke til arrangørsiden som en sak på <a href="https://github.com/jQrgen/kryptonytt/issues" rel="noopener">GitHub</a>.</p>"""
    page("kalender", "Kalender – krypto, bitcoin og blokkjede i Norge", "kalender", body, "Kommende arrangementer om krypto, bitcoin og blokkjede i Norge, med dato, sted og arrangør.")
    print(f"kalender: {len(up)} kommende, {len(past)} tidligere")

if __name__ == "__main__": build()
