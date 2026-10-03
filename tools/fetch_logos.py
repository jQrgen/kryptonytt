#!/usr/bin/env python3
"""Hentar logo (ikon) frå den offisielle nettstaden til kvar organisasjon i industrikartet og lagrar ein lokal kopi
i img/logos/. Sida lastar aldri noko frå tredjepart; kartet brukar berre dei lokale filene.
Domena står i data/logos.json -> domains (berre domene vi er sikre på er offisielle). Manglar logo, viser kartet initialar.
Logoane er varemerke for dei respektive organisasjonane og blir berre brukte for å kjenne dei att.
Køyr manuelt: python3 tools/fetch_logos.py  (tek ikkje bort eksisterande filer når ein nettstad ikkje svarar)."""
import json, os, re, sys, urllib.parse, datetime as dt, requests
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = lambda *a: os.path.join(ROOT, *a)
UA = "KryptonyttNorge/1.0 (+https://jqrgen.github.io/kryptonytt/om/)"
cfg = json.load(open(P("data", "logos.json"), encoding="utf-8"))
os.makedirs(P("img", "logos"), exist_ok=True)
EXT = {"image/png": "png", "image/svg+xml": "svg", "image/x-icon": "ico", "image/vnd.microsoft.icon": "ico", "image/jpeg": "jpg", "image/webp": "webp"}
def candidates(base, html):
    out = []
    for m in re.finditer(r"<link\b[^>]*>", html, re.I):
        t = m.group(0); rel = (re.search(r'rel=["\']([^"\']+)', t, re.I) or [None, ""])[1].lower(); href = re.search(r'href=["\']([^"\']+)', t, re.I)
        if not href or "icon" not in rel or "mask" in rel: continue
        sz = re.search(r'sizes=["\'](\d+)', t); score = (2 if "apple-touch" in rel else 1) * 1000 + (int(sz.group(1)) if sz else (180 if "apple-touch" in rel else 32))
        if href.group(1).lower().endswith(".svg"): score += 500
        out.append((score, urllib.parse.urljoin(base, href.group(1))))
    out.sort(reverse=True); return [u for _, u in out] + [urllib.parse.urljoin(base, "/apple-touch-icon.png"), urllib.parse.urljoin(base, "/favicon.ico")]
for key, dom in cfg["domains"].items():
    base = f"https://{dom}/"
    try: r = requests.get(base, headers={"User-Agent": UA}, timeout=12); html = r.text if r.ok else ""
    except Exception as e: print(f"{key}: {dom} svarar ikkje ({e.__class__.__name__})"); continue
    for u in candidates(r.url if html else base, html):
        try: ir = requests.get(u, headers={"User-Agent": UA}, timeout=12)
        except Exception: continue
        ct = ir.headers.get("content-type", "").split(";")[0].strip().lower()
        if not ir.ok or ct not in EXT or len(ir.content) < 100: continue
        fn = f"img/logos/{key}.{EXT[ct]}"
        for old in [f for f in os.listdir(P("img", "logos")) if f.startswith(key + ".")]: os.remove(P("img", "logos", old))
        open(P(fn), "wb").write(ir.content)
        cfg.setdefault("logos", {})[key] = {"file": fn, "source": u, "domain": dom, "fetched": dt.date.today().isoformat()}
        print(f"{key}: {u} -> {fn} ({len(ir.content)} B)"); break
    else: print(f"{key}: fann ingen brukbar logo på {dom}")
json.dump(cfg, open(P("data", "logos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
