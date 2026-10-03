#!/usr/bin/env python3
"""Fletter redaktørens beslutninger i queue/approved.json inn i data/news.json og data/orgchart.json.
Kjøres automatisk av publish.sh før bygging. Bare det som står som godkjent her blir publisert.

queue/approved.json:
  items:    [{"url": ..., "summary": "1–2 egne setninger", "topics": [valgfritt], "title": valgfri rettet tittel,
              "approved_by": "Kryptonytt redaktør", "approved_at": "YYYY-MM-DD"}]
  rejected: [{"url": ... | "title_contains": ..., "reason": ...}]   # holdes ute, også når feeden finner dem igjen
  entities: {"approve": [entity-id, ...], "reject": [entity-id, ...]}
  relations:{"approve": [relation-id, ...], "reject": [relation-id, ...]}
"""
import json, os, sys, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = lambda *a: os.path.join(ROOT, *a)
def load(p, d):
    try: return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError: return d
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def canon(url):
    p = urllib.parse.urlparse(url.strip())
    q = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(("utm_", "fbclid", "gclid"))])
    p = p._replace(query=q)
    return p.netloc.lower().removeprefix("www.") + (p.path.rstrip("/") or "/") + ("?" + p.query if p.query else "")
ap = load(P("queue", "approved.json"), {"items": [], "rejected": [], "entities": {"approve": [], "reject": []}, "relations": {"approve": [], "reject": []}})
news = load(P("data", "news.json"), {"items": []}); org = load(P("data", "orgchart.json"), {"entities": [], "relations": []})
by = {canon(i["url"]): i for i in news["items"]}
n_pub = n_rej = 0; missing = []
for a in ap.get("items", []):
    it = by.get(canon(a["url"]))
    if not it: missing.append(a["url"]); continue
    s = (a.get("summary") or "").strip()
    if not s: print(f"advarsel: mangler summary for {a['url']}", file=sys.stderr); continue
    it.update(status="published", summary=s, approved_by=a.get("approved_by", "Kryptonytt redaktør"), approved_at=a.get("approved_at"))
    for k in ("topics", "title", "source_name", "links"):
        if a.get(k): it[k] = a[k]
    n_pub += 1
for r in ap.get("rejected", []):
    for it in news["items"]:
        if (r.get("url") and canon(r["url"]) == canon(it["url"])) or (r.get("title_contains") and r["title_contains"].lower() in it["title"].lower()):
            it.update(status="rejected", summary=None, reject_reason=r.get("reason")); n_rej += 1
approved = {canon(a["url"]) for a in ap.get("items", [])}
for it in news["items"]:  # alt publisert som ikke lenger står som godkjent, trekkes tilbake
    if it.get("status") == "published" and canon(it["url"]) not in approved: it["status"] = "pending"
ea, er = set(ap.get("entities", {}).get("approve", [])), set(ap.get("entities", {}).get("reject", []))
for e in org["entities"]:  # industrikart-rader er allerede redaktørgodkjent (status published fra import); approve/reject overstyrer
    if e["id"] in er: e["status"] = "rejected"
    elif e["id"] in ea: e["status"] = "published"
ra, rr = set(ap.get("relations", {}).get("approve", [])), set(ap.get("relations", {}).get("reject", []))
for r in org["relations"]:
    if r["id"] in rr: r["status"] = "rejected"
    elif r["id"] in ra: r["status"] = "published"
save(P("data", "news.json"), news); save(P("data", "orgchart.json"), org)
q = load(P("queue", "review.json"), None)
if q:
    q["items_needing_summary"] = [x for x in q["items_needing_summary"] if any(i["id"] == x["id"] and i["status"] == "pending" for i in news["items"])]
    save(P("queue", "review.json"), q)
print(f"godkjenninger: {n_pub} saker publisert, {n_rej} avvist, {sum(e['status']=='published' for e in org['entities'])} entiteter og "
      f"{sum(r['status']=='published' for r in org['relations'])} relasjoner godkjent" + (f"; {len(missing)} godkjente URL-er mangler i news.json (kjør ./fetch.sh --add URL --days 60): {missing}" if missing else ""))
