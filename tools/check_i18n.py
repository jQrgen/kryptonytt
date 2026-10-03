#!/usr/bin/env python3
"""Sjekkar at alt vi sjølve skriv finst på nynorsk, bokmål og engelsk. Køyrer i nattrutinen (fetch.sh) og morgonrutinen (publish.sh).
Skriv lista til queue/review.json -> translations_needed, slik at redaktøren ser kva som manglar.
Manglar ein variant, viser nettstaden bokmål med lang="nb" (ingenting blir blokkert)."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = lambda *a: os.path.join(ROOT, *a)
def load(p, d):
    try: return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError: return d
ap = load(P("queue", "approved.json"), {}); need = []
for it in ap.get("items", []):
    miss = [k for k in ("summary", "summary_nn", "summary_en") if not (it.get(k) or "").strip()]
    if it.get("title") and (it.get("title_nn") or it.get("title_en")): miss += [k for k in ("title_nn", "title_en") if not it.get(k)]
    for l in it.get("links", []): miss += [f"links[{l.get('url')}].{k}" for k in ("label_nn", "label_en") if not l.get(k)]
    if miss: need.append({"url": it["url"], "missing": miss})
ev = ap.get("events", {})
for eid in ev.get("notes", {}):
    miss = [f"events.notes_{lg}" for lg in ("nn", "en") if not ev.get(f"notes_{lg}", {}).get(eid)]
    if miss: need.append({"event": eid, "missing": miss})
for e in load(P("endringer.json"), {"entries": []})["entries"]:
    miss = [k for k in ("text_nn", "text_en") if not e.get(k)]
    if miss: need.append({"endringslogg": e.get("text", "")[:60], "missing": miss})
rv = load(P("queue", "review.json"), None)
if rv is not None:
    rv["translations_needed"] = need
    json.dump(rv, open(P("queue", "review.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"språkvariantar: {len(need)} oppføringar manglar nynorsk/engelsk" + ("" if not need else " -> queue/review.json translations_needed"))
