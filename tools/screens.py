#!/usr/bin/env python3
"""Skjermbilder av site/ (lokal server) – brukes til QA. .venv/bin/python tools/screens.py [base-url]"""
import sys, subprocess, time, os
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base = sys.argv[1] if len(sys.argv) > 1 else None
srv = None
if not base:
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "-d", os.path.join(ROOT, "site")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); base = "http://localhost:8765/"
shots = [("skjerm/", 1080, 1920, "skjerm-hoykant-1080x1920.png"), ("skjerm/", 1920, 1080, "skjerm-liggende-1920x1080.png"),
         ("", 1280, 900, "shots/nyheter.png"), ("organisasjonskart/", 1280, 1100, "shots/organisasjonskart.png"), ("", 390, 844, "shots/mobil-nyheter.png"), ("organisasjonskart/", 390, 844, "shots/mobil-org.png"), ("kilder/", 1280, 900, "shots/kilder.png"), ("om/", 1280, 900, "shots/om.png"), ("kalender/", 1280, 1000, "shots/kalender.png"), ("kalender/", 390, 844, "shots/mobil-kalender.png")]
os.makedirs(os.path.join(ROOT, "shots"), exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    for path, w, h, out in shots:
        pg = b.new_page(viewport={"width": w, "height": h}); pg.goto(base + path); pg.wait_for_timeout(2500)
        pg.screenshot(path=os.path.join(ROOT, out)); pg.close(); print(out)
    b.close()
if srv: srv.terminate()
