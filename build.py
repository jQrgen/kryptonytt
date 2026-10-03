#!/usr/bin/env python3
"""Byggjer den statiske nettstaden i site/ på tre språk: nynorsk (hovudspråk, rot), bokmål (/bm/) og engelsk (/en/).
Berre saker med status=published og eiga oppsummering, og entitetar/relasjonar med status=published og minst
éi kjeldelenkje, kjem med. Inga sporing, ingen tredjepartsskript, ingen eksterne skrifter.
Éin førstepartsinformasjonskapsel (kn_lang) hugsar språkvalet. Synleg tekst: «kunstig intelligens», aldri AI/KI.
Sidetekstane ligg i tools/site_pages.py; denne fila held felles oppsett, sideramme og språkval."""
import json, os, re, shutil, subprocess, html, datetime as dt
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.abspath(__file__)); P = lambda *a: os.path.join(ROOT, *a)
BASE = "https://jqrgen.github.io/kryptonytt/"
SITE = os.environ.get("KN_SITE_DIR") or P("site")   # KN_SITE_DIR: scratch builds (tests), never published
OSLO = ZoneInfo("Europe/Oslo")
LANGS = {"nn": "", "nb": "bm/", "en": "en/"}          # språk -> mappe
LOCALE = {"nn": "nn_NO", "nb": "nb_NO", "en": "en_GB"}
LANGNAME = {"nn": "Nynorsk", "nb": "Bokmål", "en": "English"}
class _S: lang = "nn"
S = _S()
def L(nn, nb, en): return {"nn": nn, "nb": nb, "en": en}[S.lang]
def tr(obj, key):
    """Felt med språkvariant: key = bokmål, key_nn, key_en. Returnerer (tekst, lang-attributt). Manglar varianten, blir bokmål vist med lang="nb"."""
    if S.lang != "nb" and (obj.get(f"{key}_{S.lang}") or "").strip(): return obj[f"{key}_{S.lang}"], ""
    v = obj.get(key) or ""
    return v, ("" if S.lang == "nb" or not v else ' lang="nb"')
def load(p, d=None):
    try: return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError: return d
E = lambda s: html.escape(str(s if s is not None else ""), quote=True)
def snippets(url, title):
    return json.loads(subprocess.check_output(["node", P("tools", "snippets.js"), url, title, S.lang]))
def _flag(name, env):
    ap = load(P("queue", "approved.json"), {}) or {}
    return bool((ap.get(name) or {}).get("enabled")) or os.environ.get(env) == "1"
AKADEMIA_ON = _flag("akademia", "KRYPTONYTT_PREVIEW_AKADEMIA")
REGEL_ON = _flag("reglar", "KRYPTONYTT_PREVIEW_REGLAR")   # «Slik blir reglane til»: av til jQrgen godkjenner
def MORGEN(): return L("Nyheitene blir oppdaterte dagleg av kunstig intelligens", "Nyheter oppdateres daglig av kunstig intelligens", "News is updated daily by artificial intelligence")
MON = {"nn": ["jan.", "feb.", "mars", "april", "mai", "juni", "juli", "aug.", "sep.", "okt.", "nov.", "des."],
       "nb": ["jan.", "feb.", "mars", "april", "mai", "juni", "juli", "aug.", "sep.", "okt.", "nov.", "des."],
       "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
def nodate(iso):
    d = dt.datetime.fromisoformat(iso).astimezone(OSLO)
    return f"{d.day} {MON['en'][d.month-1]} {d.year}" if S.lang == "en" else f"{d.day}. {MON[S.lang][d.month-1]} {d.year}"
CSS = open(P("templates", "site.css"), encoding="utf-8").read()
FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%23b45309'/%3E%3Ctext x='8' y='12.5' font-size='12' text-anchor='middle' fill='white' font-family='sans-serif' font-weight='bold'%3EK%3C/text%3E%3C/svg%3E"

def paths(slug):
    """root = relativ sti til rota av nettstaden (der /bm/ og /en/ ligg), home = heimesida for dette språket."""
    up = slug.count("/") + 1 if slug else 0
    return ("../" * (up + (1 if LANGS[S.lang] else 0)) or "./"), ("../" * up or "./")

def lang_head(slug, root):
    """hreflang-alternativ, språkval-informasjonskapsel og omdirigering. Reglar:
    - eit klikk på eit språk set kn_lang (path = rota av nettstaden, dvs. /kryptonytt/ på GitHub Pages, SameSite=Lax, 1 år) og vinn alltid;
    - informasjonskapselen blir berre respektert når nokon kjem UTANFRÅ til ei nynorsk-side (standardadressa),
      aldri ved interne klikk og aldri på direkte lenkjer til /bm/ eller /en/;
    - ?lang=nn i adressa hindrar omdirigering. Utan JavaScript skjer ingenting."""
    s = (slug + "/") if slug else ""
    alts = "".join(f'<link rel="alternate" hreflang="{k}" href="{BASE}{v}{s}">' for k, v in LANGS.items()) + f'<link rel="alternate" hreflang="x-default" href="{BASE}{s}">'
    target = {k: root + v + s for k, v in LANGS.items()}
    js = ("<script>(function(){var P=" + json.dumps(S.lang) + ",A=" + json.dumps(target) + ",R;try{R=new URL(" + json.dumps(root) + ",location.href).pathname}catch(x){R='/'}"
          "function set(l){document.cookie='kn_lang='+l+'; path='+R+'; max-age=31536000; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'')}"
          "document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-setlang]');if(a)set(a.getAttribute('data-setlang'))},true);"
          "if(P!=='nn'||/[?&]lang=nn/.test(location.search))return;var m=document.cookie.match(/(?:^|; )kn_lang=(nb|en)(?:;|$)/);if(!m)return;"
          "var r=document.referrer;try{if(r&&new URL(r).origin===location.origin)return}catch(x){}location.replace(A[m[1]]+location.hash)})();</script>")
    return alts, js

def lang_nav(slug, root):
    s = (slug + "/") if slug else ""
    return ('<nav class="lang" aria-label="' + L("Språk", "Språk", "Language") + '">' + "".join(
        f'<a href="{root}{v}{s}" hreflang="{k}" lang="{k}" data-setlang="{k}"{" aria-current=true" if k == S.lang else ""}>{LANGNAME[k]}</a>' for k, v in LANGS.items()) + "</nav>")

def out_dir(slug): return os.path.join(SITE, LANGS[S.lang], slug)

def page(slug, title, nav, body, desc, extra_script=""):
    url = BASE + LANGS[S.lang] + (slug + "/" if slug else "")
    root, home = paths(slug)
    s = snippets(url, f"{title} – Kryptonytt Norge" if slug else L("Kryptonytt Norge – norske kryptonyheiter", "Kryptonytt Norge – norske kryptonyheter", "Kryptonytt Norge – Norwegian crypto news"))
    navs = ([("", L("Nyheiter", "Nyheter", "News")), ("organisasjonskart", L("Kven er kven", "Hvem er hvem", "Who’s who")), ("kalender", L("Kalender", "Kalender", "Calendar"))]
            + ([("akademia", L("Akademia", "Akademia", "Academia"))] if AKADEMIA_ON else [])
            + ([("reglar", L("Slik blir reglane til", "Slik blir reglene til", "How the rules are made"))] if REGEL_ON else [])
            + [("kilder", L("Kjelder", "Kilder", "Sources")), ("om", L("Om", "Om", "About"))])
    nav_html = "".join(f'<a href="{home}{n + "/" if n else ""}"{" aria-current=page" if n == nav else ""}>{E(t)}</a>' for n, t in navs)
    alts, ljs = lang_head(slug, root)
    import newsletter_site as NL
    footer = L(
        f'Kryptonytt Norge blir driven av Jørgen S. Notland (jQrgen), Oslo, med hjelp av kunstig intelligens. Ansvarleg redaktør: «Kryptonytt redaktør» (ein bot basert på kunstig intelligens), med jQrgen som ansvarleg person. Ingen investeringsråd. Inga sporing; éin informasjonskapsel hugsar berre språkvalet ditt. <a href="{home}om/">Om, rettingar og fjerning</a> · <a href="{home}endringer/">Endringslogg</a>.',
        f'Kryptonytt Norge drives av Jørgen S. Notland (jQrgen), Oslo, med hjelp av kunstig intelligens. Ansvarlig redaktør: «Kryptonytt redaktør» (en bot basert på kunstig intelligens), med jQrgen som ansvarlig person. Ingen investeringsråd. Ingen sporing; én informasjonskapsel husker bare språkvalget ditt. <a href="{home}om/">Om, rettelser og fjerning</a> · <a href="{home}endringer/">Endringslogg</a>.',
        f'Kryptonytt Norge is run by Jørgen S. Notland (jQrgen), Oslo, with help from artificial intelligence. Editor: “Kryptonytt redaktør” (a bot based on artificial intelligence), with jQrgen as the responsible person. No investment advice. No tracking; a single cookie only remembers your language choice. <a href="{home}om/">About, corrections and removal</a> · <a href="{home}endringer/">Changelog</a>.')
    doc = f"""<!doctype html>
<html lang="{S.lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}{" – Kryptonytt Norge" if slug else ""}</title>
<meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">{alts}
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}"><meta property="og:type" content="website"><meta property="og:locale" content="{LOCALE[S.lang]}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="icon" href="{FAVICON}">{ljs}
<style>{CSS}{s['css']}</style></head>
<body><header class="top"><div class="wrap"><a class="brand" href="{home}">Krypto<span>nytt</span> Norge</a><nav class="main" aria-label="{L("Hovudmeny", "Hovedmeny", "Main menu")}">{nav_html}</nav>{lang_nav(slug, root)}</div></header>
<main class="wrap">
{body}
{s['top']}
</main>
<footer><div class="wrap">{NL.footer(home, slug)}{footer}<p class="morgen">{E(MORGEN())}</p></div></footer>
{s['script']}{extra_script}{NL.script()}
</body></html>"""
    d = out_dir(slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(doc)

def build():
    import site_pages as SP
    ctx = SP.prepare()
    for lang in LANGS:
        S.lang = lang
        SP.build_home(ctx); SP.build_org(ctx); SP.build_sources(ctx)
        if AKADEMIA_ON: SP.build_akademia()
        if REGEL_ON:
            import rules_page; rules_page.build()
        SP.build_changelog(); SP.build_calendar(ctx); SP.build_about(); SP.build_screen()
        import newsletter_site; newsletter_site.build_newsletter()
    S.lang = "nn"
    missing = [i["id"] for i in ctx["items"] if not (i.get("summary_nn") and i.get("summary_en"))]
    print(f"build: {len(ctx['items'])} saker, {len(ctx['ents'])} entitetar ({sum(e['type']=='person' for e in ctx['ents'])} personar), {len(ctx['rels'])} relasjonar, språk: {', '.join(LANGS)} -> {SITE}")
    if missing: print(f"merk: {len(missing)} saker manglar nynorsk/engelsk oppsummering (viser bokmål): {', '.join(missing)}")

if __name__ == "__main__":
    import sys; sys.modules.setdefault("build", sys.modules["__main__"]); sys.path.insert(0, P("tools")); build()
