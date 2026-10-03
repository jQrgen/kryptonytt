#!/usr/bin/env python3
"""Arrangementer (kalender) for Kryptonytt Norge. Kalles fra fetch.py ved hver henting, eller alene:
  .venv/bin/python events.py                     # søk etter nye arrangementer i event_sources (sources.json)
  .venv/bin/python events.py --add-event URL     # legg til fra arrangørens side (JSON-LD eller iCal) – researcher
Regler (redaktør): bare arrangementer der arrangørens egen side eller en offentlig oppføring viser dato, sted og arrangør,
og som faktisk handler om krypto, bitcoin eller blokkjede. Betalte/sponsede merkes. Aldri oppdiktede arrangementer.
Nye funn får status "pending" med mindre kilden er en ren kryptoarrangør (trusted) OG dato, sted og arrangør er funnet.
Redaktøren godkjenner/avviser i queue/approved.json -> events.approve / events.reject (id)."""
import argparse, datetime as dt, hashlib, json, os, re, sys, urllib.parse
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
OSLO = ZoneInfo("Europe/Oslo")
ROOT = os.path.dirname(os.path.abspath(__file__)); P = lambda *a: os.path.join(ROOT, *a)

def _load(p, d):
    try: return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError: return d
def _save(p, d):
    t = p + ".tmp"; json.dump(d, open(t, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(t, p)
def parse_dt(s):
    if not s: return None
    s = s.strip()
    m = re.fullmatch(r"(\d{8})T(\d{6})(Z?)", s)
    if m:
        d = dt.datetime.strptime(m[1] + m[2], "%Y%m%d%H%M%S")
        return (d.replace(tzinfo=dt.timezone.utc) if m[3] else d.replace(tzinfo=OSLO)).astimezone(OSLO)
    if re.fullmatch(r"\d{8}", s): return dt.datetime.strptime(s, "%Y%m%d").replace(tzinfo=OSLO)
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return (d if d.tzinfo else d.replace(tzinfo=OSLO)).astimezone(OSLO)
    except ValueError: return None
def jsonld_events(html):
    s = BeautifulSoup(html, "lxml"); out = []
    for sc in s.find_all("script", type="application/ld+json"):
        try: d = json.loads(sc.string or "")
        except Exception: continue
        for x in (d if isinstance(d, list) else d.get("@graph", [d])):
            if not isinstance(x, dict) or "Event" not in str(x.get("@type")): continue
            loc = x.get("location") or {}; loc = loc[0] if isinstance(loc, list) and loc else loc
            online = "OnlineEventAttendanceMode" in str(x.get("eventAttendanceMode")) or (isinstance(loc, dict) and loc.get("@type") == "VirtualLocation")
            addr = loc.get("address") if isinstance(loc, dict) else None
            city = (addr.get("addressLocality") if isinstance(addr, dict) else None)
            lname = loc.get("name") if isinstance(loc, dict) else (loc if isinstance(loc, str) else None)
            street = addr.get("streetAddress") if isinstance(addr, dict) else None
            parts = [v.strip() for v in [lname, street] if isinstance(v, str) and v.strip()]
            parts = [v for v in parts if not any(v != w and v in w for w in parts)]
            place = ", ".join(dict.fromkeys(parts)) or None
            org = x.get("organizer") or {}; org = org[0] if isinstance(org, list) and org else org
            offers = x.get("offers") or {}; offers = offers if isinstance(offers, list) else [offers]
            prices = [float(o.get("price")) for o in offers if isinstance(o, dict) and str(o.get("price", "")).replace(".", "", 1).isdigit()]
            out.append({"title": x.get("name"), "start": parse_dt(x.get("startDate")), "end": parse_dt(x.get("endDate")), "place": place or None,
                        "city": city, "online": online, "organiser": org.get("name") if isinstance(org, dict) else None,
                        "url": x.get("url"), "description": BeautifulSoup(x.get("description") or "", "lxml").get_text(" ")[:400],
                        "paid": (max(prices) > 0) if prices else None})
    return out
def ics_events(text):
    out = []; text = re.sub(r"\r?\n[ \t]", "", text)
    for blk in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        f = {}
        for line in blk.strip().splitlines():
            if ":" in line: k, v = line.split(":", 1); f[k.split(";")[0].upper()] = v.replace("\\,", ",").replace("\\n", " ").strip()
        out.append({"title": f.get("SUMMARY"), "start": parse_dt(f.get("DTSTART")), "end": parse_dt(f.get("DTEND")), "place": f.get("LOCATION"),
                    "city": None, "online": False, "organiser": None, "url": f.get("URL"), "description": f.get("DESCRIPTION", "")[:400], "paid": None})
    return out
def eid(e): return hashlib.sha1(f"{(e.get('url') or '').split('?')[0]}|{e['start'].date() if e.get('start') else ''}|{(e.get('title') or '').lower()}".encode()).hexdigest()[:12]
CITIES = ["Oslo", "Bergen", "Trondheim", "Stavanger", "Kristiansand", "Tromsø", "Bodø", "Drammen", "Fredrikstad", "Ålesund", "Fornebu", "Lillehammer", "Arendal", "Haugesund"]
def guess_city(place):
    for c in CITIES:
        if place and re.search(rf"\b{c}\b", place): return c
    return None

def run(get, robots_ok, matches, log, cfg, add_url=None, a=None):
    data = _load(P("data", "events.json"), {"events": []}); by = {e["id"]: e for e in data["events"]}
    status = _load(P("state", "source_status.json"), {}); now = dt.datetime.now(OSLO); new = []
    def take(ev, src, trusted):
        if not ev.get("title") or not ev.get("start"): return
        text = f"{ev['title']} {ev.get('description', '')}"
        if not trusted and not matches(text): return
        ev["organiser"] = ev.get("organiser") or src.get("organiser")
        ev["city"] = ev.get("city") or guess_city(ev.get("place")) or src.get("city")
        if ev.get("url") is None: ev["url"] = src.get("page") or src["url"]
        ev["paid"] = ev["paid"] if ev.get("paid") is not None else ev.get("paid_hint")
        i = eid(ev)
        if i in by:
            for k in ("place", "city", "end", "organiser"):
                v = ev.get(k)
                if v: by[i][k] = v.isoformat() if hasattr(v, "isoformat") else v
            return
        complete = bool(ev.get("place") or ev.get("online")) and bool(ev.get("organiser"))
        rec = {"id": i, "title": ev["title"], "start": ev["start"].isoformat(), "end": ev["end"].isoformat() if ev.get("end") else None,
               "place": ev.get("place"), "city": ev.get("city"), "online": bool(ev.get("online")), "organiser": ev.get("organiser"),
               "url": ev["url"], "source": src["name"], "source_url": src.get("page") or src["url"], "paid": ev.get("paid"), "sponsored": None,
               "found": now.isoformat(timespec="seconds"), "status": "published" if (trusted and complete) else "pending",
               "note": None if complete else "mangler sted eller arrangør – sjekk arrangørens side"}
        data["events"].append(rec); by[i] = rec; new.append(rec)
    def fetch_page(u):
        if not robots_ok(u): raise RuntimeError("robots.txt tillater ikke")
        r = get(u); r.raise_for_status(); return r
    sources = cfg.get("event_sources", [])
    if add_url:
        r = fetch_page(add_url); evs = jsonld_events(r.text)
        if not evs:
            s = BeautifulSoup(r.text, "lxml"); ic = next((x["href"] for x in s.find_all("a", href=True) if re.search(r"ical|\.ics", x["href"], re.I)), None)
            if ic: evs = ics_events(fetch_page(urllib.parse.urljoin(add_url, ic)).text)
        src = {"name": a.source_name or urllib.parse.urlparse(add_url).netloc.removeprefix("www."), "url": add_url, "page": add_url, "organiser": a.organiser, "city": a.city}
        if not evs and a.title and a.start:
            evs = [{"title": a.title, "start": parse_dt(a.start), "end": parse_dt(a.end) if a.end else None, "place": a.place, "city": a.city, "online": bool(a.online),
                    "organiser": a.organiser, "url": add_url, "description": "", "paid": a.paid}]
        for ev in evs:
            if a.paid is not None: ev["paid"] = a.paid
            take(ev, src, True)
        for n in new: n["status"] = "pending"; n["note"] = "lagt til manuelt – redaktør må godkjenne"
        log(f"arrangement: {len(new)} lagt til fra {add_url}" if new else f"arrangement: fant ingen nye med dato på {add_url} (bruk --title/--start/--place/--organiser)")
    else:
        for src in sources:
            if not src.get("enabled", True): continue
            err = None; n0 = len(new); n_found = 0
            try:
                r = fetch_page(src["url"])
                if src["type"] == "jsonld":
                    evs = jsonld_events(r.text); n_found = len(evs)
                    for ev in evs: take(ev, src, src.get("trusted", False))
                elif src["type"] == "listing-ical":
                    s = BeautifulSoup(r.text, "lxml")
                    links = {urllib.parse.urljoin(src["url"], x["href"]) for x in s.find_all("a", href=True)
                             if re.search(src["link_pattern"], x["href"]) and (src.get("trusted") or matches(x.get_text(" ") + " " + x["href"].replace("-", " ")))}
                    for u in sorted(links)[:20]:
                        pg = fetch_page(u); ps = BeautifulSoup(pg.text, "lxml")
                        ic = next((x["href"] for x in ps.find_all("a", href=True) if re.search(r"download-ical|\.ics", x["href"], re.I)), None)
                        if not ic: continue
                        price = re.search(r"kr\.?\s?(\d[\d .]*),?-?", ps.get_text(" "))
                        for ev in ics_events(fetch_page(urllib.parse.urljoin(u, ic)).text):
                            n_found += 1; ev["paid_hint"] = True if price and int(re.sub(r"\D", "", price[1]) or 0) > 0 else None
                            ev["description"] = ps.get_text(" ")[:1500]; src2 = dict(src, page=u); take(ev, src2, src.get("trusted", False))
            except Exception as ex: err = f"{type(ex).__name__}: {ex}"[:200]
            status["ev-" + src["id"]] = {"checked": now.isoformat(timespec="seconds"), "ok": err is None, "entries": n_found, "error": err}
            log(f"arrangement {src['id']:<18} funnet={n_found} nye={len(new) - n0} err={err}")
    data["events"].sort(key=lambda e: e["start"]); data["updated"] = now.isoformat(timespec="seconds")
    _save(P("data", "events.json"), data); _save(P("state", "source_status.json"), status)
    q = _load(P("queue", "review.json"), {"items_needing_summary": [], "candidate_entities": []})
    apev = (_load(P("queue", "approved.json"), {}) or {}).get("events", {}); done = set(apev.get("approve", [])) | set(apev.get("reject", []))
    q["events_pending"] = [e for e in data["events"] if e["status"] == "pending" and e["id"] not in done and e["start"] >= now.isoformat()]
    _save(P("queue", "review.json"), q)
    log(f"arrangementer: {len(new)} nye, {sum(e['status']=='published' for e in data['events'])} publisert, {len(q['events_pending'])} venter på redaktør")
    return new

if __name__ == "__main__":
    import fetch
    ap = argparse.ArgumentParser(); ap.add_argument("--add-event", metavar="URL"); ap.add_argument("--source-name"); ap.add_argument("--organiser")
    ap.add_argument("--title"); ap.add_argument("--start", help="YYYY-MM-DDTHH:MM (Oslo-tid)"); ap.add_argument("--end"); ap.add_argument("--place"); ap.add_argument("--city")
    ap.add_argument("--online", action="store_true"); ap.add_argument("--paid", type=lambda s: s.lower() in ("1", "true", "ja", "yes"), default=None)
    a = ap.parse_args()
    run(fetch.get, fetch.robots_ok, lambda t: bool(fetch.matches(t)), fetch.log, fetch.CFG, a.add_event, a)
