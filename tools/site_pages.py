"""Sidene på Kryptonytt Norge (nyheiter, kven er kven + industrikart, kjelder, om, skjerm). Kallast frå build.py éin gong per språk.
Tekstar: L(nynorsk, bokmål, engelsk). Synleg tekst: «kunstig intelligens» / «artificial intelligence», aldri AI eller KI."""
import json, os, re, shutil, subprocess, datetime as dt
import build as B
from build import L, tr, E, P, S, load, page, paths, nodate, out_dir, LANGS, BASE, OSLO
GH = '<a href="https://github.com/jQrgen/kryptonytt/issues" rel="noopener">GitHub</a>'
TOPICS = {"bitcoin": ("Bitcoin", "Bitcoin", "Bitcoin"), "blokkjede": ("Blokkjede", "Blokkjede", "Blockchain"), "krypto": ("Krypto", "Krypto", "Crypto"),
          "regulering": ("Regulering", "Regulering", "Regulation"), "selskaper": ("Selskap", "Selskaper", "Companies")}
def topic(t): return L(*TOPICS[t]) if t in TOPICS else t

def prepare():
    subprocess.run([os.sys.executable, P("tools", "import_industrikart.py")], check=True)
    subprocess.run([os.sys.executable, P("tools", "apply_approvals.py")], check=True)
    if B.AKADEMIA_ON: subprocess.run([os.sys.executable, P("tools", "import_akademia.py")], check=True)
    news = load(P("data", "news.json"), {"items": []}); org = load(P("data", "orgchart.json"), {"entities": [], "relations": []})
    cfg = load(P("sources.json")); status = load(P("state", "source_status.json"), {})
    if os.path.exists(B.SITE): shutil.rmtree(B.SITE)
    os.makedirs(os.path.join(B.SITE, "data"))
    items = [i for i in news["items"] if i.get("status") == "published" and (i.get("summary") or "").strip()]
    items.sort(key=lambda i: i["published"], reverse=True)
    keys = ("id", "url", "title", "title_nn", "title_en", "source", "source_name", "published", "topics", "summary", "summary_nn", "summary_en", "paywall", "links")
    pub_items = [{k: i[k] for k in keys if k in i} for i in items]
    ents = [dict(e) for e in org["entities"] if e.get("status") == "published" and e.get("sources")]
    eids = {e["id"] for e in ents}
    rels = [r for r in org["relations"] if r.get("status") == "published" and r.get("sources") and r["from"] in eids and r["to"] in eids]
    for e in ents:  # regel: «kunstig intelligens» i synleg tekst, aldri KI/AI (gjeld våre eigne skildringar, ikkje kjeldetitlar)
        for k in ("description", "role"):
            if e.get(k): e[k] = re.sub(r"\bKI/HPC\b", "kunstig intelligens og HPC", re.sub(r"\bKI-", "kunstig intelligens-", e[k]))
    for e in ents:  # profilar: berre godkjende lenkjer med kjelde
        pr = [p for p in e.get("profiles", []) if p.get("url") and p.get("source") and p.get("status") == "published"]
        for k in ("verification", "verification_nb", "verification_en", "origin"): e.pop(k, None)  # interne notat for redaktøren, ikkje publiserte
        if pr: e["profiles"] = [{k: p[k] for k in ("kind", "url", "source") if k in p} for p in pr]
        else: e.pop("profiles", None)
    logos = (load(P("data", "logos.json"), {}) or {}).get("logos", {})
    json.dump({"updated": news.get("updated"), "items": pub_items}, open(os.path.join(B.SITE, "data", "news.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pub_org = {"updated": org.get("updated"), "entities": ents, "relations": rels}
    json.dump(pub_org, open(os.path.join(B.SITE, "data", "orgchart.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for e in ents:  # bilete (berre dei som blir brukte og har lisens)
        im = e.get("image")
        if im and im.get("file") and im.get("license"):
            dst = os.path.join(B.SITE, im["file"]); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(P(im["file"]), dst)
    for lg in logos.values():
        if os.path.exists(P(lg["file"])):
            dst = os.path.join(B.SITE, lg["file"]); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(P(lg["file"]), dst)
    active = sorted({s["name"].split(" (")[0] for s in cfg["sources"] if s.get("enabled") and s["type"] not in ("bing",) and (s["type"] == "search" or status.get(s["id"], {}).get("ok", True))})
    json.dump({"active": active}, open(os.path.join(B.SITE, "data", "sources.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from site_pages2 import events_for_site
    evs, now = events_for_site()
    json.dump({"events": [e for e in evs if not e["past"]]}, open(os.path.join(B.SITE, "data", "events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(B.SITE, ".nojekyll"), "w").close()
    open(os.path.join(B.SITE, "robots.txt"), "w").write("User-agent: *\nAllow: /\n")
    return dict(news=news, org=org, cfg=cfg, status=status, items=items, ents=ents, rels=rels, pub_org=pub_org, logos=logos, evs=evs, now=now)

def build_home(ctx):
    items, news = ctx["items"], ctx["news"]
    srcs = sorted({(i["source"], i["source_name"]) for i in items}, key=lambda x: x[1].lower())
    lis = []
    for i in items:
        tags = "".join(f'<span class="tag">{E(topic(t))}</span>' for t in i["topics"])
        pw = ' · <span class="pw">' + L("kan krevje abonnement", "kan kreve abonnement", "may require a subscription") + '</span>' if i.get("paywall") else ""
        # Eigen tittel finst berre når vi sjølve har omsett/retta han; elles står kjelda sin tittel urørt.
        title, tl = tr(i, "title") if (i.get("title_nn") or i.get("title_en")) else (i["title"], "")
        summ, sl = tr(i, "summary")
        links = "".join(f'<div class="meta">↳ <a href="{E(l["url"])}" rel="noopener" target="_blank"{tr(l, "label")[1]}>{E(tr(l, "label")[0])}</a></div>' for l in i.get("links", []))
        lis.append(f'<li data-src="{E(i["source"])}" data-topics="{E(" ".join(i["topics"]))}"><h3{tl}><a href="{E(i["url"])}" rel="noopener" target="_blank">{E(title)}</a></h3>'
                   f'<div class="meta"><b>{E(i["source_name"])}</b> · <time datetime="{E(i["published"])}">{nodate(i["published"])}</time>{pw} {tags}</div>'
                   f'<p class="sum"{sl}>{E(summ)}</p>{links}</li>')
    opts = "".join(f'<option value="{E(k)}">{E(n)}</option>' for k, n in srcs)
    chips = "".join(f'<button type="button" class="chip" data-t="{k}" aria-pressed="false">{E(topic(k))}</button>' for k in TOPICS)
    upd = nodate(news["updated"]) if news.get("updated") else ""
    n = len(items)
    body = L(
        f"""<h1>Norske nyheiter om bitcoin, blokkjede og krypto</h1>
<p class="meta"><a href="skjerm/">Skjermmodus for kontorskjerm (fullskjerm, ståande eller liggjande) →</a></p>
<p class="lead">Lenkjer til norske saker frå aviser, styresmakter, bloggar og podkastar, med ei kort oppsummering skriven av redaksjonen. Les heile saka hos kjelda. Sist oppdatert {upd}. {n} saker.</p>""",
        f"""<h1>Norske nyheter om bitcoin, blokkjede og krypto</h1>
<p class="meta"><a href="skjerm/">Skjermmodus for kontorskjerm (fullskjerm, høykant eller liggende) →</a></p>
<p class="lead">Lenker til norske saker fra aviser, myndigheter, blogger og podkaster, med en kort oppsummering skrevet av redaksjonen. Les hele saken hos kilden. Sist oppdatert {upd}. {n} saker.</p>""",
        f"""<h1>Norwegian news about bitcoin, blockchain and crypto</h1>
<p class="meta"><a href="skjerm/">Screen mode for office displays (full screen, portrait or landscape) →</a></p>
<p class="lead">Links to Norwegian stories from newspapers, authorities, blogs and podcasts, each with a short summary written by our editors. Read the full story at the source. Headlines are shown as the source published them, so most are in Norwegian. Last updated {upd}. {n} stories.</p>""")
    body += f"""
<div class="filters" role="group" aria-label="Filter"><label for="fsrc">{L("Kjelde", "Kilde", "Source")}</label><select id="fsrc"><option value="">{L("Alle kjelder", "Alle kilder", "All sources")}</option>{opts}</select>
<label>{L("Tema", "Tema", "Topic")}</label><div class="chips">{chips}</div><span id="count" class="meta" aria-live="polite"></span></div>
<p class="morgen">{E(B.MORGEN())}</p>
<ol class="news" id="news">{''.join(lis) or '<li class="empty">' + L("Ingen publiserte saker enno.", "Ingen publiserte saker ennå.", "No published stories yet.") + '</li>'}</ol>
<p class="notice">{L("Oppsummeringane er våre eigne, skrivne ut frå tittel og ingress. Vi attgjev ikkje artikkeltekst. Saker merkte «kan krevje abonnement» ligg hos ei avis med betalingsmur. Ingenting her er investeringsråd.",
"Oppsummeringene er våre egne, skrevet ut fra tittel og ingress. Vi gjengir ikke artikkeltekst. Saker merket «kan kreve abonnement» ligger hos en avis med betalingsmur. Ingenting her er investeringsråd.",
"The summaries are our own, written from the headline and standfirst. We do not reproduce article text. Stories marked “may require a subscription” are behind a newspaper paywall. Nothing here is investment advice.")}</p>"""
    js = """<script>
(function(){var sel=document.getElementById('fsrc'),chips=[].slice.call(document.querySelectorAll('.chip')),lis=[].slice.call(document.querySelectorAll('#news li[data-src]')),cnt=document.getElementById('count');
function apply(push){var s=sel.value,t=chips.filter(function(c){return c.getAttribute('aria-pressed')==='true'}).map(function(c){return c.dataset.t}),n=0;
lis.forEach(function(li){var ok=(!s||li.dataset.src===s)&&(!t.length||t.some(function(x){return (' '+li.dataset.topics+' ').indexOf(' '+x+' ')>=0}));li.hidden=!ok;if(ok)n++});
cnt.textContent=n+' WORD';if(push){var p=new URLSearchParams();if(s)p.set('kilde',s);if(t.length)p.set('tema',t.join(','));history.replaceState(null,'',p.toString()?'#'+p:location.pathname)}}
var p=new URLSearchParams(location.hash.slice(1));if(p.get('kilde'))sel.value=p.get('kilde');(p.get('tema')||'').split(',').forEach(function(x){chips.forEach(function(c){if(c.dataset.t===x)c.setAttribute('aria-pressed','true')})});
sel.addEventListener('change',function(){apply(1)});chips.forEach(function(c){c.addEventListener('click',function(){c.setAttribute('aria-pressed',c.getAttribute('aria-pressed')==='true'?'false':'true');apply(1)})});apply(0)})();
</script>""".replace("WORD", L("saker", "saker", "stories"))
    page("", L("Kryptonytt Norge – norske nyheiter om bitcoin, blokkjede og krypto", "Kryptonytt Norge – norske nyheter om bitcoin, blokkjede og krypto", "Kryptonytt Norge – Norwegian news about bitcoin, blockchain and crypto"), "", body,
         L("Norske nyheiter om bitcoin, blokkjede og kryptovaluta samla på éin stad, med kjelder og eit organisasjonskart over kven som er kven i norsk krypto.",
           "Norske nyheter om bitcoin, blokkjede og kryptovaluta samlet på ett sted, med kilder og et organisasjonskart over hvem er hvem i norsk krypto.",
           "Norwegian news about bitcoin, blockchain and cryptocurrency in one place, with sources and an org chart of who’s who in Norwegian crypto."), js)

ORG_T = {
 "nn": {"link": "Kopling til {} sektor", "privat": "privat", "offentlig": "offentleg", "Privat sektor": "Privat sektor", "Offentlig sektor": "Offentleg sektor", "Annet": "Anna", "Personer": "Personar",
        "Foto": "Foto", "kilde": "kjelde", "Se bilde hos kilden": "Sjå bilete hos kjelda", "sak": "sak", "Lukk": "Lukk", "Person": "Person", "Organisasjon": "Organisasjon",
        "nettside": "nettside", "Koblinger": "Koplingar", "Kilder": "Kjelder", "Offentlig": "Offentleg", "Privat": "Privat", "Profiler": "Offentlege profilar", "linksrc": "kjelde for lenkja", "venter": "ventar på redaktør"},
 "nb": {"link": "Kobling til {} sektor", "privat": "privat", "offentlig": "offentlig", "Privat sektor": "Privat sektor", "Offentlig sektor": "Offentlig sektor", "Annet": "Annet", "Personer": "Personer",
        "Foto": "Foto", "kilde": "kilde", "Se bilde hos kilden": "Se bilde hos kilden", "sak": "sak", "Lukk": "Lukk", "Person": "Person", "Organisasjon": "Organisasjon",
        "nettside": "nettside", "Koblinger": "Koblinger", "Kilder": "Kilder", "Offentlig": "Offentlig", "Privat": "Privat", "Profiler": "Offentlige profiler", "linksrc": "kilde for lenken", "venter": "venter på redaktør"},
 "en": {"link": "Link to the {} sector", "privat": "private", "offentlig": "public", "Privat sektor": "Private sector", "Offentlig sektor": "Public sector", "Annet": "Other", "Personer": "People",
        "Foto": "Photo", "kilde": "source", "Se bilde hos kilden": "See photo at the source", "sak": "story", "Lukk": "Close", "Person": "Person", "Organisasjon": "Organisation",
        "nettside": "website", "Koblinger": "Connections", "Kilder": "Sources", "Offentlig": "Public", "Privat": "Private", "Profiler": "Public profiles", "linksrc": "source for this link", "venter": "awaiting editor"}}
GROUP_T = {"Børser/meglere": ("Børsar/meklarar", "Exchanges/brokers"), "Banker": ("Bankar", "Banks"), "Betaling": ("Betaling", "Payments"), "Investorer/fond": ("Investorar/fond", "Investors/funds"),
           "Medier": ("Medium", "Media"), "Organisasjoner": ("Organisasjonar", "Organisations"), "Selskaper/startups": ("Selskap/oppstartsselskap", "Companies/start-ups"),
           "Utvinning/datasentre": ("Utvinning/datasenter", "Mining/data centres"), "EU": ("EU", "EU"), "Regelverk": ("Regelverk", "Legislation"),
           "Storting og regjering": ("Storting og regjering", "Parliament and government"), "Tilsyn og etater": ("Tilsyn og etatar", "Supervisors and agencies")}
def group_name(g):
    if S.lang == "nb" or g not in GROUP_T: return g
    return GROUP_T[g][0 if S.lang == "nn" else 1]

# Industrikart: kategoriar (nøkkel, nn, nb, en, fargeklasse) og kva gruppe i organisasjonskartet som høyrer til kvar.
ICATS = [("bors", "Børsar og meklarar", "Børser og meglere", "Exchanges and brokers", "priv"),
         ("forvaring", "Lommebøker og forvaring", "Lommebøker og oppbevaring", "Wallets and custody", "priv"),
         ("infra", "Infrastruktur og utvinning", "Infrastruktur og utvinning", "Infrastructure and mining", "priv"),
         ("betaling", "Betaling", "Betaling", "Payments", "priv"),
         ("bank", "Bank og finans", "Bank og finans", "Banks and finance", "priv"),
         ("radgjeving", "Rådgjeving, juss og revisjon", "Rådgivning, juss og revisjon", "Consulting, legal and audit", "priv"),
         ("media", "Medium, foreiningar og miljø", "Medier, foreninger og miljøer", "Media and communities", "priv"),
         ("internasjonal", "Internasjonale aktørar i Noreg", "Internasjonale aktører i Norge", "International players in Norway", "priv"),
         ("akademia", "Akademia", "Akademia", "Academia", "aka"),
         ("offentleg", "Offentleg sektor", "Offentlig sektor", "Public sector", "pub")]
GROUP2CAT = {"Børser/meglere": "bors", "Utvinning/datasentre": "infra", "Betaling": "betaling", "Banker": "bank", "Investorer/fond": "bank",
             "Selskaper/startups": "bank", "Medier": "media", "Organisasjoner": "media"}
PUB_SUB = [("Tilsyn og etater", "Tilsyn og etatar", "Tilsyn og etater", "Supervisors and agencies"), ("Storting og regjering", "Storting og departement", "Storting og departementer", "Parliament and ministries"),
           ("EU", "EU-organ", "EU-organer", "EU bodies"), ("Regelverk", "Regelverk", "Regelverk", "Legislation")]
INST_KEY = {"NTNU": "inst-ntnu", "UiO": "inst-uio", "Universitetet i Oslo": "inst-uio", "BI": "inst-bi", "Handelshøyskolen BI": "inst-bi", "NHH": "inst-nhh", "UiB": "inst-uib",
            "Universitetet i Bergen": "inst-uib", "HVL": "inst-hvl", "Høgskulen på Vestlandet": "inst-hvl", "UiA": "inst-uia", "Universitetet i Agder": "inst-uia", "OsloMet": "inst-oslomet", "USN": "inst-usn"}
def initials(n):
    i = "".join(w[0] for w in re.split(r"[\s\-–/()]+", n) if w and w[0].isalnum())[:2].upper()
    return n[:2].upper() if i in ("AI", "KI") else i  # regel: aldri «AI»/«KI» i synleg tekst

def industry_map(ctx, root, home):
    logos = ctx["logos"]; ents = [e for e in ctx["ents"] if e["type"] != "person"]
    def tile(key, name, href):
        lg = logos.get(key)
        im = f'<img src="{root}{E(lg["file"])}" alt="" loading="lazy" width="40" height="40">' if lg else f'<span class="mono" aria-hidden="true">{E(initials(name))}</span>'
        return f'<a class="tile" href="{href}">{im}<span>{E(name)}</span></a>'
    cats = {k: [] for k, *_ in ICATS}; pub = {g[0]: [] for g in PUB_SUB}
    for e in sorted(ents, key=lambda e: e["name"].lower()):
        c = e.get("industry") or ("offentleg" if e["sector"] == "offentlig" else GROUP2CAT.get(e.get("group"), "media"))
        t = tile(e["id"], e["name"], f'#{E(e["id"])}')
        if c == "offentleg": pub[e.get("group") if e.get("group") in pub else "Tilsyn og etater"].append(t)
        else: cats[c].append(t)
    if B.AKADEMIA_ON:  # akademia: institusjonar med godkjende rader på Akademia-sida (lenkjer dit)
        a = load(P("data", "akademia.json"), {}) or {}; seen = {}
        for k in ("courses", "research", "publications", "groups"):
            for r in a.get(k, []):
                if r.get("status") != "godkjent": continue
                for part in re.split(r"[,/;()]| og ", r.get("institution") or ""):
                    key = INST_KEY.get(part.strip())
                    if key and key not in seen: seen[key] = part.strip()
        cats["akademia"] = [tile(k, n, f"{home}akademia/") for k, n in sorted(seen.items(), key=lambda x: x[1].lower())]
    out = []
    for k, nn, nb, en, cls in ICATS:
        name = L(nn, nb, en)
        if k == "offentleg":
            inner = "".join(f'<div class="sub">{E(L(a, b, c))}</div><div class="tiles">{"".join(pub[g])}</div>' for g, a, b, c in PUB_SUB if pub.get(g))
            out.append(f'<section class="icat {cls} wide" aria-label="{E(name)}"><h3>{E(name)}</h3>{inner}</section>')
        elif cats.get(k):
            out.append(f'<section class="icat {cls}" aria-label="{E(name)}"><h3>{E(name)}</h3><div class="tiles">{"".join(cats[k])}</div></section>')
        else:
            out.append(f'<section class="icat {cls} empty"><h3>{E(name)}</h3><p>{L("Ingen kjeldebelagde aktørar i kartet enno.", "Ingen kildebelagte aktører i kartet ennå.", "No sourced organisations in the map yet.")}</p></section>')
    if any("kaupr.io/pages" in x.get("url", "") for e in ents for x in e.get("sources", [])):  # openheit: Kaupr er kjelde (ikkje sponsor)
        out.append('<p class="meta kaupr-note">' + L("Nokre aktørar er henta frå Kaupr sine Onchain Pages. Kvar slik aktør er sjekka mot selskapet si eiga nettside eller offentlege register (Brønnøysund, ESMA) før han kom med, og Kaupr er oppgitt som kjelde.",
            "Noen aktører er hentet fra Kauprs Onchain Pages. Hver slik aktør er sjekket mot selskapets egen nettside eller offentlige registre (Brønnøysund, ESMA) før den kom med, og Kaupr er oppgitt som kilde.",
            "Some organisations come from Kaupr’s Onchain Pages. Each one was checked against the company’s own website or public registers (Brønnøysund, ESMA) before being included, and Kaupr is credited as a source.") + '</p>')
    return '<div class="imap">' + "".join(out) + "</div>"

def build_org(ctx):
    org, pub_org = ctx["org"], ctx["pub_org"]
    root, home = paths("organisasjonskart")
    summ = org.get("summary") or []
    nbnote = "" if S.lang == "nb" else f'<p class="meta">{L("Skildringane, rollene og oversikta under kjem frå researcharbeidet vårt og står på bokmål.", "", "The descriptions, roles and overview below come from our research and are in Norwegian (Bokmål).")}</p>'
    rules = f' · <a href="{home}reglar/">{L("Slik blir reglane til →", "Slik blir reglene til →", "How the rules are made →")}</a>' if B.REGEL_ON else ""
    body = f"""<h1>{L("Kven er kven i norsk krypto", "Hvem er hvem i norsk krypto", "Who’s who in Norwegian crypto")}</h1>
<p class="lead">{L("Selskap, organisasjonar, styresmakter og personar i offentlege yrkesroller, slik dei er omtalte i nyheitene vi lenkjer til. Kvar oppføring og kvar kopling har lenkje til kjelda. Klikk på eit kort for detaljar og koplingar på tvers av privat og offentleg sektor.",
"Selskaper, organisasjoner, myndigheter og personer i offentlige yrkesroller, slik de er omtalt i nyhetene vi lenker til. Hver oppføring og hver kobling har lenke til kilden. Klikk på et kort for detaljer og koblinger på tvers av privat og offentlig sektor.",
"Companies, organisations, authorities and people in public professional roles, as covered in the news we link to. Every entry and every connection links to its source. Click a card for details and links across the private and public sectors.")}</p>
<p class="meta"><a href="#industrikart">{L("Industrikart: aktørane etter kategori ↓", "Industrikart: aktørene etter kategori ↓", "Industry map: organisations by category ↓")}</a>{rules}</p>
{nbnote}
<p class="meta kaupr-note">{L(f'Openheit: Aktørar henta frå Kaupr sine Onchain Pages er sjekka mot eiga nettside eller offentlege register, og Kaupr er oppgitt som kjelde. <a href="{home}om/#sponsor">Meir om dette</a>.',
f'Åpenhet: Aktører hentet fra Kauprs Onchain Pages er sjekket mot egen nettside eller offentlige registre, og Kaupr er oppgitt som kilde. <a href="{home}om/#sponsor">Mer om dette</a>.',
f'Disclosure: Organisations taken from Kaupr’s Onchain Pages were checked against their own websites or public registers, and Kaupr is credited as a source. <a href="{home}om/#sponsor">More about this</a>.')}</p>
{('<details class="notice" open lang="nb"><summary><b>' + L("Oversikt: slik heng norsk kryptoregulering og -bransje saman", "Oversikt: slik henger norsk kryptoregulering og -bransje sammen", "Overview: how Norwegian crypto regulation and the industry fit together") + '</b> (' + L("per", "per", "as of") + ' ' + E(org.get("updated") or "") + ')</summary>' + "".join(f"<p>{E(x)}</p>" for x in summ) + '</details>') if summ else ''}
{('<details class="notice" lang="nb"><summary>' + L("Atterhald", "Forbehold", "Caveats") + '</summary><ul>' + "".join(f"<li>{E(x)}</li>" for x in org.get("caveats", [])) + '</ul></details>') if org.get("caveats") else ''}
<div class="filters"><div class="seg" role="group" aria-label="{L("Vis sektor", "Vis sektor", "Show sector")}"><button type="button" data-v="begge" aria-pressed="true">{L("Begge", "Begge", "Both")}</button><button type="button" data-v="privat" aria-pressed="false">{ORG_T[S.lang]["Privat sektor"]}</button><button type="button" data-v="offentlig" aria-pressed="false">{ORG_T[S.lang]["Offentlig sektor"]}</button></div>
<label for="osearch">{L("Søk", "Søk", "Search")}</label><input type="search" id="osearch" placeholder="{L("Namn, rolle, organisasjon", "Navn, rolle, organisasjon", "Name, role, organisation")}"></div>
<div id="chart" class="cols"><noscript>{L("Kartet krev JavaScript; sjå industrikartet og lista under.", "Kartet krever JavaScript; se industrikartet og listen under.", "The chart needs JavaScript; see the industry map and the list below.")}</noscript></div>
<section id="detail" hidden aria-live="polite"></section>
<h2 id="industrikart">{L("Industrikart", "Industrikart", "Industry map")}</h2>
<p class="lead">{L("Aktørane i organisasjonskartet sorterte etter kategori. Klikk på ein aktør for å opne oppføringa i kartet over.", "Aktørene i organisasjonskartet sortert etter kategori. Klikk på en aktør for å åpne oppføringen i kartet over.", "The organisations in the org chart grouped by category. Click one to open its entry in the chart above.")}{rules}</p>
{industry_map(ctx, root, home)}
<p class="meta">{L("Logoane er varemerke for dei respektive organisasjonane, er henta frå deira eigne nettstader og ligg lokalt hos oss. Utan logo viser vi initialar.", "Logoene er varemerker for de respektive organisasjonene, er hentet fra deres egne nettsteder og ligger lokalt hos oss. Uten logo viser vi initialer.", "Logos are trademarks of their respective organisations, taken from their own websites and hosted locally by us. Where we have no logo we show initials.")}</p>
<h2 id="liste">{L("Søkbar liste", "Søkbar liste", "Searchable list")}</h2>
<table class="list" id="olist"><thead><tr><th>{L("Namn", "Navn", "Name")}</th><th>Type</th><th>Sektor</th><th>{L("Rolle / skildring", "Rolle / beskrivelse", "Role / description")}</th><th>{L("Kjelder", "Kilder", "Sources")}</th></tr></thead><tbody></tbody></table>
<p class="notice">{L(f'Vi tek berre med det som står i kjeldene: namn, offentleg yrkesrolle, organisasjon og profilar personen sjølv har gjort offentlege. Ingen private opplysningar. Bilete blir berre viste når dei har fri lisens (Wikimedia Commons) eller er pressebilete som eksplisitt kan brukast; elles viser vi initialar og lenkjer til biletet hos kjelda. Feil? Sjå <a href="{home}om/#rettelser">rettingar og fjerning</a>.',
f'Vi tar bare med det som står i kildene: navn, offentlig yrkesrolle, organisasjon og profiler personen selv har gjort offentlige. Ingen private opplysninger. Bilder vises bare når de har fri lisens (Wikimedia Commons) eller er pressebilder som eksplisitt kan brukes; ellers viser vi initialer og lenker til bildet hos kilden. Feil? Se <a href="{home}om/#rettelser">rettelser og fjerning</a>.',
f'We only include what the sources state: name, public professional role, organisation and profiles the person has made public. No private details. Photos are shown only when freely licensed (Wikimedia Commons) or explicitly released press photos; otherwise we show initials and link to the photo at the source. Spotted an error? See <a href="{home}om/#rettelser">corrections and removal</a>.')}</p>
<script id="orgdata" type="application/json">{json.dumps(pub_org, ensure_ascii=False).replace("</", "<\\/")}</script>"""
    if S.lang == "en": body = body.replace("<th>Sektor</th>", "<th>Sector</th>")
    T = dict(ORG_T[S.lang]); T["groups"] = {g: group_name(g) for g in GROUP_T}; T["locale"] = S.lang
    js = f"<script>var KN_ROOT={json.dumps(root)},KN_T={json.dumps(T, ensure_ascii=False)};</script><script>" + open(P("tools", "orgchart.js"), encoding="utf-8").read() + "</script>"
    page("organisasjonskart", L("Kven er kven i norsk krypto", "Hvem er hvem i norsk krypto", "Who’s who in Norwegian crypto"), "organisasjonskart", body,
         L("Organisasjonskart og industrikart over norsk krypto: selskap, organisasjonar, styresmakter og personar i offentlege roller, med kjeldelenkjer.",
           "Organisasjonskart og industrikart over norsk krypto: selskaper, organisasjoner, myndigheter og personer i offentlige roller, med kildelenker.",
           "Org chart and industry map of Norwegian crypto: companies, organisations, authorities and people in public roles, with source links."), js)

KIND_T = {"Allmennkringkaster": ("Allmennkringkastar", "Public broadcaster"), "Finans": ("Finans", "Finance"), "Kringkaster": ("Kringkastar", "Broadcaster"), "Kryptoblogg": ("Kryptoblogg", "Crypto blog"),
          "Kryptomedie (nordisk)": ("Kryptomedium (nordisk)", "Crypto media (Nordic)"), "Lokalavis": ("Lokalavis", "Local newspaper"), "Myndighet": ("Styresmakt", "Authority"),
          "Nyhetsavis": ("Nyheitsavis", "News outlet"), "Næringsliv": ("Næringsliv", "Business"), "Podkast": ("Podkast", "Podcast"), "Regionavis": ("Regionavis", "Regional newspaper"),
          "Selskapsblogg": ("Selskapsblogg", "Company blog"), "Selskapsmelding": ("Selskapsmelding", "Company announcements"), "Søkefeed": ("Søkjefeed", "Search feed"),
          "Teknologi": ("Teknologi", "Technology"), "Teknologi/gründer": ("Teknologi/gründer", "Technology/start-ups"), "Ukeavis": ("Vekeavis", "Weekly newspaper")}
def build_sources(ctx):
    cfg, status = ctx["cfg"], ctx["status"]
    rows = []
    for s in cfg["sources"]:
        st = status.get(s["id"], {})
        if s["type"] == "search": cls, lab = "ok", L("via nyheitssøk", "via nyhetssøk", "via news search")
        elif s.get("enabled") and st.get("ok", True): cls, lab = "ok", L("blir overvaka", "overvåkes", "monitored")
        elif s.get("search_fallback"): cls, lab = "bad", L("RSS verkar ikkje (via nyheitssøk)", "RSS virker ikke (via nyhetssøk)", "RSS broken (via news search)")
        else: cls, lab = "bad", L("verkar ikkje", "virker ikke", "not working")
        feed = f'<a href="{E(s["feed"])}" rel="noopener">feed</a>' if s.get("feed") and "{q}" not in s["feed"] else (L("søk", "søk", "search") if s.get("feed") else "–")
        kind = s["kind"] if S.lang == "nb" or s["kind"] not in KIND_T else KIND_T[s["kind"]][0 if S.lang == "nn" else 1]
        note = s.get("status", "")
        rows.append(f'<tr><td><a href="{E(s["url"])}" rel="noopener" target="_blank">{E(s["name"])}</a></td><td>{E(kind)}</td><td>{feed}</td>'
                    f'<td class="{cls}">{lab}</td><td{"" if S.lang == "nb" or not note else " lang=nb"}>{E(note)}</td></tr>')
    bs = next((s for s in cfg["sources"] if s["type"] == "bing"), {})
    ns = len(bs.get("sites", []))
    qs = bs.get("queries", []) + [L(f"«{t}» på {ns} norske nettstader", f"«{t}» på {ns} norske nettsteder", f"“{t}” on {ns} Norwegian websites") for t in bs.get("site_terms", [])]
    d = cfg.get("min_delay_seconds", 2)
    body = L(
f"""<h1>Kjelder vi følgjer</h1>
<p class="lead">Aviser, styresmakter, bloggar og podkastar vi hentar overskrifter frå. Vi les RSS-feedar og eit nyheitssøk, følgjer robots.txt, identifiserer oss med ein eigen brukaragent og held minst {d} sekund mellom førespurnader til same nettstad. Vi hentar aldri artikkeltekst bak betalingsmur. Merknadene står på bokmål.</p>""",
f"""<h1>Kilder vi følger</h1>
<p class="lead">Aviser, myndigheter, blogger og podkaster vi henter overskrifter fra. Vi leser RSS-feeder og et nyhetssøk, følger robots.txt, identifiserer oss med en egen brukeragent og holder minst {d} sekunder mellom forespørsler til samme nettsted. Vi henter aldri artikkeltekst bak betalingsmur.</p>""",
f"""<h1>Sources we follow</h1>
<p class="lead">Newspapers, authorities, blogs and podcasts we collect headlines from. We read RSS feeds and a news search, respect robots.txt, identify ourselves with our own user agent and wait at least {d} seconds between requests to the same website. We never fetch article text behind a paywall. The notes column is in Norwegian.</p>""")
    body += f"""
<table class="list"><thead><tr><th>{L("Kjelde", "Kilde", "Source")}</th><th>Type</th><th>Feed</th><th>Status</th><th>{L("Merknad", "Merknad", "Notes")}</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>{L("Søkjeord i nyheitssøket", "Søkeord i nyhetssøket", "Search terms in the news search")}</h2><p class="prose">{E(", ".join(qs))}. {L("Frå søket tek vi berre med saker frå norske domene (.no), og lenkja går alltid direkte til originalsaka.", "Fra søket tar vi bare med saker fra norske domener (.no), og lenken går alltid direkte til originalsaken.", "From the search we only include stories from Norwegian domains (.no), and the link always goes straight to the original story.")}</p>
<h2>{L("Nøkkelord", "Nøkkelord", "Keywords")}</h2><p class="prose">{L("Ei sak blir teken med når tittel eller ingress nemner til dømes", "En sak tas med når tittel eller ingress nevner for eksempel", "A story is included when its headline or standfirst mentions, for example,")} bitcoin, krypto, kryptovaluta, blokkjede, blockchain, NFT, stablecoin, MiCA, sentralbankpenger, Bare Bitcoin, Firi, Bitmynt, K33, NBX {L("eller", "eller", "or")} Nexa. {L("Redaksjonen går gjennom alle treff før dei blir publiserte.", "Redaksjonen går gjennom alle treff før de publiseres.", "Our editors review every match before it is published.")}</p>
<p class="meta">{L(f"Manglar ei kjelde? Føreslå ho som ei sak på {GH}.", f"Mangler en kilde? Foreslå den som en sak på {GH}.", f"Missing a source? Suggest it as an issue on {GH}.")}</p>"""
    page("kilder", L("Kjelder", "Kilder", "Sources"), "kilder", body, L("Norske aviser, styresmakter, bloggar og podkastar som Kryptonytt Norge følgjer.", "Norske aviser, myndigheter, blogger og podkaster som Kryptonytt Norge følger.", "Norwegian newspapers, authorities, blogs and podcasts that Kryptonytt Norge follows."))

def build_about():
    body = open(P("templates", {"nn": "om.nn.html", "nb": "om.html", "en": "om.en.html"}[S.lang]), encoding="utf-8").read().replace("__ROOT__", paths("om")[0])
    page("om", L("Om Kryptonytt Norge", "Om Kryptonytt Norge", "About Kryptonytt Norge"), "om", body,
         L("Om Kryptonytt Norge: kven som står bak, redaksjonell policy, rettingar og fjerning.", "Om Kryptonytt Norge: hvem som står bak, redaksjonell policy, rettelser og fjerning.", "About Kryptonytt Norge: who is behind it, editorial policy, corrections and removal."))

SKJERM_T = [  # (bokmål i malen, nynorsk, engelsk); None = uendra
 ("Skjermmodus – Kryptonytt Norge", None, "Screen mode – Kryptonytt Norge"),
 ("Fullskjerm-visning av Kryptonytt Norge for kontorskjerm.", "Fullskjermvising av Kryptonytt Norge for kontorskjerm.", "Full-screen view of Kryptonytt Norge for office displays."),
 ("⛶ Fullskjerm<", None, "⛶ Full screen<"), ("'⛶ Fullskjerm'", None, "'⛶ Full screen'"), ("'Avslutt fullskjerm'", None, "'Exit full screen'"),
 (">Lyst tema<", None, ">Light theme<"), ("?'Mørkt tema':'Lyst tema'", None, "?'Dark theme':'Light theme'"),
 ("Til nettstedet", "Til nettstaden", "To the website"), (">Siste nyheter<", ">Siste nyheiter<", ">Latest news<"), (">Hvem er hvem<", ">Kven er kven<", ">Who’s who<"),
 (">Kommende arrangementer<", ">Komande arrangement<", ">Upcoming events<"), (">Kilder vi følger<", ">Kjelder vi følgjer<", ">Sources we follow<"),
 ("Laster …", "Lastar …", "Loading …"),
 ("Oppsummeringer: redaksjonen, laget med hjelp av kunstig intelligens. Ingen investeringsråd. Ingen sporing.", "Oppsummeringar: redaksjonen, laga med hjelp av kunstig intelligens. Ingen investeringsråd. Inga sporing.", "Summaries: our editors, made with help from artificial intelligence. No investment advice. No tracking."),
 ("Ingen saker ennå.", "Ingen saker enno.", "No stories yet."), ("'Side '", None, "'Page '"), ("' av '", None, "' of '"), ("' saker'", None, "' stories'"),
 ("'Offentlig sektor':'Privat sektor'", "'Offentleg sektor':'Privat sektor'", "'Public sector':'Private sector'"), (">Foto: '", None, ">Photo: '"), (">Kilde: '", ">Kjelde: '", ">Source: '"),
 ("aktører i privat sektor", "aktørar i privat sektor", "private-sector organisations"), ("i offentlig sektor", "i offentleg sektor", "in the public sector"),
 ("personer i offentlige roller", "personar i offentlege roller", "people in public roles"), ("kildebelagte koblinger", "kjeldebelagde koplingar", "sourced connections"),
 ("'Digitalt'", None, "'Online'"), (">Betalt<", None, ">Paid<"), (">Sponset<", ">Sponsa<", ">Sponsored<"),
 ("'Sist oppdatert: '", None, "'Last updated: '"), ("'ukjent'", "'ukjend'", "'unknown'"), ("' · data hentet '", "' · data henta '", "' · data fetched '"),
 ("'Kunne ikke hente data – prøver igjen om 5 minutter'", "'Kunne ikkje hente data – prøver igjen om 5 minutt'", "'Could not fetch data – trying again in 5 minutes'"),
 ("['januar','februar','mars','april','mai','juni','juli','august','september','oktober','november','desember']", None, "['January','February','March','April','May','June','July','August','September','October','November','December']"),
 ("['søndag','mandag','tirsdag','onsdag','torsdag','fredag','lørdag']", "['sundag','måndag','tysdag','onsdag','torsdag','fredag','laurdag']", "['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']"),
]
def build_screen():
    root, home = paths("skjerm")
    t = open(P("templates", "skjerm.html"), encoding="utf-8").read()
    if S.lang != "nb":
        for nb, nn, en in SKJERM_T:
            assert nb in t, f"skjerm-mal: finn ikkje {nb!r}"
            new = nn if S.lang == "nn" else en
            if new is not None: t = t.replace(nb, new)
    if S.lang == "en":
        t = t.replace("return d.getDate()+'. '+M[d.getMonth()]", "return d.getDate()+' '+M[d.getMonth()]").replace("D[d.getDay()]+' '+d.getDate()+'. '+M[d.getMonth()]", "D[d.getDay()]+' '+d.getDate()+' '+M[d.getMonth()]")
    loc = {"nn": "nn-NO", "nb": "nb-NO", "en": "en-GB"}[S.lang]
    t = t.replace("'no-NO'", f"'{loc}'").replace("'nb-NO'", f"'{loc}'")
    t = t.replace('<html lang="no">', f'<html lang="{S.lang}">').replace('href="__BASE__skjerm/">', f'href="{BASE}{LANGS[S.lang]}skjerm/">' + B.lang_head("skjerm", root)[0])
    t = t.replace("'../data/", f"'{root}data/").replace("src=\"../'", f"src=\"{root}'").replace('<a href="../"', f'<a href="{home}"')
    if S.lang != "nb":  # eigne oppsummeringar og titlar på rett språk
        t = t.replace("esc(i.title)", f"esc(i.title_{S.lang}||i.title)").replace("esc(i.summary)", f"esc(i.summary_{S.lang}||i.summary)")
    tmap = {k: topic(k) for k in TOPICS}
    t = t.replace("'<span class=\"tag\">'+esc(t)+'</span>'", "'<span class=\"tag\">'+esc(TOPIC[t]||t)+'</span>'").replace("var DATA=", f"var TOPIC={json.dumps(tmap, ensure_ascii=False)},DATA=", 1)
    d = out_dir("skjerm"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(t)

from site_pages2 import build_changelog, build_akademia, build_calendar  # noqa: E402
