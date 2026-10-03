#!/usr/bin/env python3
"""Lager data/akademia.json på nytt ved hver bygging.
Eneste kilde: research/akademia.md (researcherens tabeller i industrikart-formatet: én tabell per seksjon med Kilde, Sjekket og
Status ✅/🟡/❌). Underseksjoner som «Vurdert, ikke tatt med» hoppes over. data/akademia_seed.json brukes IKKE lenger.
Researcherens status er verifisering; publisering styres av redaktøren i queue/approved.json -> "akademia": {"approve": [], "reject": []}.
Bare godkjente rader vises på siden."""
import json, os, re, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = lambda *a: os.path.join(ROOT, *a)
def load(p, d):
    try: return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError: return d
def slug(s): return re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()).strip("-")[:60]
SECTIONS = [("courses", r"emne|studieprogram|kurs"), ("groups", r"linjeforen|student"), ("publications", r"publikasjon|artikl"), ("research", r"forskning|prosjekt|miljø")]
COLS = [("code", r"^(emnekode|kode)$"), ("authors", r"forfatter"), ("year", r"^år$|årstall"), ("doi", r"^doi"), ("nva", r"^nva|cristin"),
        ("institution", r"institusjon|lærested|universitet|tilknytning"), ("level", r"nivå|studiepoeng|^stp"), ("last_activity", r"siste dokumenterte"),
        ("activity", r"^aktivitet$"), ("venue", r"tidsskrift|kanal"), ("checked", r"sjekket"), ("status", r"^status$"), ("offered", r"^tilbys"),
        ("funding", r"type|finansiering"), ("period", r"^periode"), ("source", r"kilde|lenke|url"),
        ("about", r"beskrivelse|^om$|innhold|^hva|i pensum|relevans|fokus"), ("name", r"^(emne|navn|tittel|emnenavn|prosjekt|forening|gruppe)$")]
def cell_urls(c): return [next(g for g in m.groups() if g) for m in re.finditer(r"<(https?://[^>]+)>|\]\((https?://[^)]+)\)|(https?://[^\s;|]+)", c)]
def cell_url(c):
    m = re.search(r"<(https?://[^>]+)>|\]\((https?://[^)]+)\)|(https?://\S+)", c); return next((g for g in m.groups() if g), None) if m else None
def clean(c): return re.sub(r"\*\*|(?<!\w)\*(?=\w)|(?<=\w)\*(?!\w)", "", re.sub(r"<https?://[^>]+>|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", c)).strip()
def norm_status(s):
    s = (s or "").lower()
    if "avvist" in s: return "avvist"
    if "godkjent" in s: return "godkjent med forbehold" if "forbehold" in s else "godkjent"
    return "venter på redaktør"
def key(sec, r):
    if sec == "publications": return (r.get("doi") or r.get("url") or r.get("title") or "").lower().replace("https://doi.org/", "")
    if sec == "courses" and r.get("code"): return (r["code"] + "|" + (r.get("institution") or "")).lower()
    return (r.get("name") or r.get("url") or "").lower()
def parse_md(path):
    out = {s: [] for s, _ in SECTIONS}; sec = None; hdr = None
    for line in open(path, encoding="utf-8"):
        if line.startswith("#"):
            h = line.strip("# \n").lower(); hdr = None
            if line.startswith("### "): sec = None if re.search(r"vurdert|ikke tatt med|ikke funnet", h) else sec; continue
            sec = next((s for s, rx in SECTIONS if re.search(rx, h)), None); continue
        if not sec or not line.startswith("|"): hdr = None if not line.startswith("|") else hdr; continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if hdr is None: hdr = [next((f for f, rx in COLS if re.search(rx, c.lower())), None) for c in cells]; continue
        if all(re.fullmatch(r":?-+:?", c) for c in cells): continue
        r = {}
        for f, c in zip(hdr, cells):
            if not f: continue
            if f in ("source", "doi", "nva"):
                us = cell_urls(c); u = us[0] if us else (f"https://doi.org/{c.strip()}" if f == "doi" and c.strip().startswith("10.") else None)
                if f == "doi": r["doi"] = clean(c); r["url"] = u or r.get("url")
                elif f == "nva": r["nva"] = u
                else: r["source"] = u; r["sources"] = us; r.setdefault("url", u)
            elif f == "authors": r["authors"] = [a.strip().rstrip("*").strip() for a in re.split(r";|,(?![^()]*\))", clean(c)) if a.strip()]
            else: r[f] = clean(c)
        if sec == "publications" and "name" in r: r["title"] = r.pop("name")
        if not (r.get("source") or r.get("url")): continue   # regel: hver rad må ha kildelenke
        r["verification"] = r.pop("status", "") or ""; r["status"] = "venter på redaktør"; r["origin"] = "researcher"
        if r.get("activity"): r["activity"] = "aktiv" if r["activity"].lower().startswith("aktiv") else "inaktiv"
        out[sec].append(r)
    return out
def main():
    ap = (load(P("queue", "approved.json"), {}) or {}).get("akademia", {})
    md = P("research", "akademia.md"); res = parse_md(md) if os.path.exists(md) else {}
    out = {"updated": None, "from_research": os.path.exists(md)}
    if out["from_research"]:
        m = re.search(r"per (\d{2}\.\d{2}\.\d{4})", open(md, encoding="utf-8").readline()); out["updated"] = m and m.group(1)
    for sec, _ in SECTIONS:
        rows = {}
        for r in res.get(sec, []): rows[key(sec, r)] = {**rows.get(key(sec, r), {}), **r}
        lst = []
        for r in rows.values():
            r["id"] = slug(sec[:3] + "-" + (r.get("code") or r.get("doi") or r.get("name") or r.get("title") or ""))
            if r["id"] in ap.get("approve", []): r["status"] = "godkjent"
            if r["id"] in ap.get("reject", []): r["status"] = "avvist"
            lst.append(r)
        out[sec] = sorted(lst, key=lambda r: (-(int(r.get("year") or 0)), r.get("institution") or "", r.get("code") or r.get("name") or r.get("title") or ""))
    json.dump(out, open(P("data", "akademia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("akademia: " + ", ".join(f"{s}={len(out[s])} (godkjent {sum(r['status']=='godkjent' for r in out[s])}, avvist {sum(r['status']=='avvist' for r in out[s])})" for s, _ in SECTIONS)
          + ("" if out["from_research"] else " – research/akademia.md finnes ikke"))
if __name__ == "__main__": main()
