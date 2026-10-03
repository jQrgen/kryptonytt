#!/usr/bin/env python3
"""Test av språkval og informasjonskapsel + skjermbilete på nynorsk, bokmål og engelsk.
Køyr: .venv/bin/python tools/i18n_check.py  (serverer site/ under /kryptonytt/ som på GitHub Pages)"""
import os, sys, subprocess, time, tempfile
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tmp = tempfile.mkdtemp(); os.symlink(os.path.join(ROOT, "site"), os.path.join(tmp, "kryptonytt"))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "-d", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
B = "http://localhost:8766/kryptonytt/"
ok = True
def check(name, cond):
    global ok; ok &= bool(cond); print(("OK  " if cond else "FEIL") + " " + name)
try:
    with sync_playwright() as p:
        br = p.chromium.launch()
        c = br.new_context(); pg = c.new_page()
        pg.goto(B); check("ny besøkjande: nynorsk på rota", pg.url == B and pg.locator("html").get_attribute("lang") == "nn")
        pg.click("nav.lang a[data-setlang=en]"); pg.wait_for_load_state()
        ck = {x["name"]: x for x in c.cookies()}
        check("klikk English -> /en/", pg.url == B + "en/")
        check("kn_lang=en, path=/kryptonytt/, SameSite=Lax, ~1 år", ck.get("kn_lang", {}).get("value") == "en" and ck["kn_lang"]["path"] == "/kryptonytt/" and ck["kn_lang"]["sameSite"] == "Lax" and ck["kn_lang"]["expires"] - time.time() > 360 * 86400)
        pg.click("nav.main a[href$='kalender/']"); pg.wait_for_load_state(); check("intern lenkje på engelsk", pg.url == B + "en/kalender/")
        pg2 = c.new_page(); pg2.goto(B + "kalender/"); pg2.wait_for_load_state(); check("seinare besøk utanfrå på nynorsk-side -> engelsk", pg2.url == B + "en/kalender/")
        pg2.goto(B + "bm/kilder/"); check("direkte lenkje til /bm/ blir ikkje omdirigert", pg2.url == B + "bm/kilder/")
        pg2.goto(B + "om/?lang=nn"); check("?lang=nn hindrar omdirigering", pg2.url.startswith(B + "om/"))
        pg2.goto(B + "en/"); pg2.click("nav.lang a[data-setlang=nn]"); pg2.wait_for_load_state()
        check("klikk Nynorsk vinn (ingen omdirigering tilbake)", pg2.url == B and {x["name"]: x["value"] for x in c.cookies()}.get("kn_lang") == "nn")
        pg3 = c.new_page(); pg3.goto(B + "organisasjonskart/"); check("etter val av nynorsk: blir verande på nynorsk", pg3.url == B + "organisasjonskart/")
        reqs = []; pg4 = br.new_page(); pg4.on("request", lambda r: reqs.append(r.url))
        for path in ("", "bm/", "en/", "organisasjonskart/", "en/organisasjonskart/", "en/skjerm/"): pg4.goto(B + path); pg4.wait_for_timeout(600)
        check("ingen tredjepartsførespurnader", all(u.startswith("http://localhost:8766/") or u.startswith("data:") for u in reqs))
        for path in ("", "bm/", "en/"):
            pg4.goto(B + path); hl = pg4.eval_on_selector_all("link[rel=alternate][hreflang]", "els=>els.map(e=>e.hreflang).join(',')")
            check(f"hreflang på /{path}: {hl}", hl == "nn,nb,en,x-default")
        br.close()
        if "--shots" in sys.argv:
            out = os.path.join(ROOT, "shots", "i18n"); os.makedirs(out, exist_ok=True)
            br = p.chromium.launch()
            jobs = []
            for lg, pre in (("nynorsk", ""), ("bokmal", "bm/"), ("english", "en/")):
                jobs += [(pre, 1280, 900, f"{lg}-forside-desktop.png", None), (pre, 390, 844, f"{lg}-forside-mobil.png", None),
                         (pre + "organisasjonskart/", 1280, 1000, f"{lg}-kven-er-kven-desktop.png", None), (pre + "organisasjonskart/", 390, 844, f"{lg}-kven-er-kven-mobil.png", None),
                         (pre + "organisasjonskart/", 1280, 1400, f"{lg}-industrikart-desktop.png", "#industrikart"), (pre + "organisasjonskart/", 390, 1600, f"{lg}-industrikart-mobil.png", "#industrikart"),
                         (pre + "kalender/", 1280, 1000, f"{lg}-kalender-desktop.png", None), (pre + "kalender/", 390, 844, f"{lg}-kalender-mobil.png", None)]
                if os.path.exists(os.path.join(ROOT, "site", pre, "reglar", "index.html")):
                    jobs += [(pre + "reglar/", 1280, 1300, f"{lg}-reglar-desktop.png", None), (pre + "reglar/", 390, 1600, f"{lg}-reglar-mobil.png", None)]
            for path, w, h, fn, anchor in jobs:
                pg = br.new_page(viewport={"width": w, "height": h}); pg.goto(B + path + "?lang=nn"); pg.wait_for_timeout(1200)
                if anchor: pg.evaluate(f"document.querySelector('{anchor}').scrollIntoView()"); pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(out, fn)); pg.close(); print(os.path.join(out, fn))
            br.close()
finally:
    srv.terminate()
sys.exit(0 if ok else 1)
