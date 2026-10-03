#!/usr/bin/env python3
"""Vekesamandrag (nyheitsbrev) for Kryptonytt Norge, laga BERRE frå godkjende saker: les data/news.json frå eit bygg av
nettstaden (standard site/, som berre har publiserte saker med eiga oppsummering). Skriv Markdown (lim inn i Substack),
rein tekst og enkel e-post-HTML til newsletter/out/ (gitignored). Sender ingenting.
Bruk: .venv/bin/python newsletter/digest.py [--lang nn|nb|en] [--days 7] [--until ÅÅÅÅ-MM-DD] [--site-dir site]
Språkregel: norsk tekst seier «kunstig intelligens», aldri AI eller KI (blir sjekka før fila blir skriven)."""
import argparse, datetime as dt, html, json, os, re
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://jqrgen.github.io/kryptonytt/"; HOME = {"nn": BASE, "nb": BASE + "bm/", "en": BASE + "en/"}; OSLO = ZoneInfo("Europe/Oslo")
MON = {"nn": "jan. feb. mars april mai juni juli aug. sep. okt. nov. des.".split(), "nb": "jan. feb. mars april mai juni juli aug. sep. okt. nov. des.".split(),
       "en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()}
T = {
 "nn": dict(h="Kryptonytt Norge – veka som gjekk", intro="Norske nyheiter om bitcoin, blokkjede og krypto som redaktøren vår har godkjent denne veka. Kvar sak lenkjer til kjelda.",
            pay="kan krevje abonnement", spons="Kaupr er sponsor", more="Alle sakene, kalenderen og kven er kven", none="Ingen godkjende saker denne veka.",
            foot="Kryptonytt Norge blir driven av Jørgen S. Notland (jQrgen), Oslo, med hjelp av kunstig intelligens. Ansvarleg redaktør: «Kryptonytt redaktør» (ein bot basert på kunstig intelligens), med jQrgen som ansvarleg person. Ingen investeringsråd.",
            kaupr="Openheit: Kaupr (kaupr.io) er sponsor av Kryptonytt og ei av kjeldene våre.", why="Du får denne e-posten fordi du har abonnert på nyheitsbrevet frå Kryptonytt Norge.", unsub="Meld av"),
 "nb": dict(h="Kryptonytt Norge – uka som gikk", intro="Norske nyheter om bitcoin, blokkjede og krypto som redaktøren vår har godkjent denne uka. Hver sak lenker til kilden.",
            pay="kan kreve abonnement", spons="Kaupr er sponsor", more="Alle sakene, kalenderen og hvem er hvem", none="Ingen godkjente saker denne uka.",
            foot="Kryptonytt Norge drives av Jørgen S. Notland (jQrgen), Oslo, med hjelp av kunstig intelligens. Ansvarlig redaktør: «Kryptonytt redaktør» (en bot basert på kunstig intelligens), med jQrgen som ansvarlig person. Ingen investeringsråd.",
            kaupr="Åpenhet: Kaupr (kaupr.io) er sponsor av Kryptonytt og en av kildene våre.", why="Du får denne e-posten fordi du har abonnert på nyhetsbrevet fra Kryptonytt Norge.", unsub="Meld av"),
 "en": dict(h="Kryptonytt Norge – the week in review", intro="Norwegian news about bitcoin, blockchain and crypto that our editor approved this week. Each item links to the source.",
            pay="may require a subscription", spons="Kaupr is a sponsor", more="All stories, the calendar and the who’s who", none="No approved stories this week.",
            foot="Kryptonytt Norge is run by Jørgen S. Notland (jQrgen), Oslo, with help from artificial intelligence. Editor: “Kryptonytt redaktør” (a bot based on artificial intelligence), with jQrgen as the responsible person. No investment advice.",
            kaupr="Disclosure: Kaupr (kaupr.io) sponsors Kryptonytt and is one of our sources.", why="You get this email because you subscribed to the Kryptonytt Norge newsletter.", unsub="Unsubscribe"),
}
NO_AIKI = re.compile(r"(?<![\w-])(?:AI|KI)(?![\w])")
def day(lang, d): return f"{d.day} {MON['en'][d.month-1]} {d.year}" if lang == "en" else f"{d.day}. {MON[lang][d.month-1]} {d.year}"
def summ(i, lang): return (i.get("summary_nn") if lang == "nn" else i.get("summary_en") if lang == "en" else None) or i.get("summary") or ""

def render(items, lang, since, until):
    s = T[lang]; rng = f"{day(lang, since)} – {day(lang, until)}"
    md = [f"# {s['h']}", f"*{rng}*", "", s["intro"], ""]; tx = [s["h"], rng, "", s["intro"], ""]
    hm = [f'<h1 style="font-size:24px;margin:0 0 4px">{html.escape(s["h"])}</h1><p style="color:#4B5563;margin:0 0 12px">{html.escape(rng)}</p><p>{html.escape(s["intro"])}</p>']
    for i in items:
        meta = [i.get("source_name") or i.get("source"), day(lang, i["_d"])]
        if i.get("paywall") in (True, "True"): meta.append(s["pay"])
        if i.get("source") == "kaupr": meta.append(s["spons"])
        md += [f"**[{i['title']}]({i['url']})**  ", f"{summ(i, lang)}  ", f"*{' · '.join(meta)}*", ""]
        tx += [i["title"], summ(i, lang), " · ".join(meta), i["url"], ""]
        hm.append(f'<p style="margin:0 0 14px"><a href="{html.escape(i["url"])}" style="font-weight:bold;color:#b45309">{html.escape(i["title"])}</a><br>{html.escape(summ(i, lang))}<br><span style="color:#4B5563;font-size:13px">{html.escape(" · ".join(meta))}</span></p>')
    if not items: md += [s["none"], ""]; tx += [s["none"], ""]; hm.append(f"<p>{html.escape(s['none'])}</p>")
    md += [f"[{s['more']}]({HOME[lang]})", "", "---", "", s["kaupr"], "", s["foot"], "", f"*{s['why']}*", ""]
    tx += [f"{s['more']}: {HOME[lang]}", "", "--", s["kaupr"], "", s["foot"], "", s["why"], "{{unsubscribe}}", ""]
    hm.append(f'<p><a href="{HOME[lang]}">{html.escape(s["more"])}</a></p><hr style="border:0;border-top:1px solid #d1d5db"><p style="font-size:13px;color:#4B5563">{html.escape(s["kaupr"])}</p>'
              f'<p style="font-size:13px;color:#4B5563">{html.escape(s["foot"])}</p><p style="font-size:13px;color:#4B5563">{html.escape(s["why"])} <a href="{{{{unsubscribe}}}}">{s["unsub"]}</a></p>')
    page = f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{html.escape(s["h"])}</title></head><body style="margin:0;padding:20px;font:16px/1.5 Arial,sans-serif;color:#111"><div style="max-width:640px;margin:0 auto">{"".join(hm)}</div></body></html>\n'
    return "\n".join(md), "\n".join(tx), page

def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--lang", default="nn", choices=list(T)); a.add_argument("--days", type=int, default=7)
    a.add_argument("--until"); a.add_argument("--site-dir", default=os.path.join(ROOT, "site")); a.add_argument("--out", default=os.path.join(ROOT, "newsletter", "out"))
    o = a.parse_args(argv)
    news = json.load(open(os.path.join(o.site_dir, "data", "news.json"), encoding="utf-8"))
    until = dt.date.fromisoformat(o.until) if o.until else dt.datetime.now(OSLO).date(); since = until - dt.timedelta(days=o.days - 1)
    items = []
    for i in news["items"]:
        if i.get("status", "published") != "published" or not summ(i, o.lang).strip(): continue
        d = dt.datetime.fromisoformat(i["published"]).astimezone(OSLO).date()
        if since <= d <= until: items.append(dict(i, _d=d))
    items.sort(key=lambda i: i["published"], reverse=True)
    md, tx, hp = render(items, o.lang, since, until)
    if o.lang in ("nn", "nb"):
        own = [m.group(0) for m in NO_AIKI.finditer(re.sub(r"https?://\S+", "", md)) if not any(m.group(0) in i["title"] for i in items)]
        if own: raise SystemExit(f"digest: «AI»/«KI» i vår eigen norske tekst: {own}")
    os.makedirs(o.out, exist_ok=True); stem = os.path.join(o.out, f"digest-{until:%Y-%m-%d}-{o.lang}")
    for ext, body in (("md", md), ("txt", tx), ("html", hp)): open(f"{stem}.{ext}", "w", encoding="utf-8").write(body)
    print(f"digest: {len(items)} godkjende saker {since}–{until} ({o.lang}) -> {stem}.md/.txt/.html")
    return stem

if __name__ == "__main__": main()
