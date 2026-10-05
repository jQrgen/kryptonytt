#!/usr/bin/env python3
"""Artikkelarkiv (berre tillegg, aldri sletting) for alt Kryptonytt nokon gong har publisert.
  archive/articles.db   SQLite (gitignored), skjema i archive/schema.sql (felles med Crypto Nordic, D1-kompatibelt)
  archive/articles.json eksport til repoet som reservekopi
Bruk:
  python3 tools/article_archive.py record [--at ISO]   # morgonrutinen: les site/data/news.json etter publisering
  python3 tools/article_archive.py backfill            # gh-pages-historikken (.publish) + data/news.json
  python3 tools/article_archive.py export
"""
import json, os, sqlite3, subprocess, sys, urllib.parse, datetime as dt
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = lambda *a: os.path.join(ROOT, *a)
SITE_ID = "kryptonytt"; DB = P("archive", "articles.db"); OSLO = ZoneInfo("Europe/Oslo")
TRACK = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid", "igshid", "ref_src", "_hsenc", "_hsmi", "yclid", "msclkid")
def canon(u):
    p = urllib.parse.urlsplit(u.strip()); host = (p.hostname or "").lower().removeprefix("www.")
    q = sorted((k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith(TRACK))
    return urllib.parse.urlunsplit(("https", host, p.path.rstrip("/") or "/", urllib.parse.urlencode(q), ""))
def now(): return dt.datetime.now(OSLO).isoformat(timespec="seconds")
def db():
    os.makedirs(P("archive"), exist_ok=True); c = sqlite3.connect(DB); c.executescript(open(P("archive", "schema.sql"), encoding="utf-8").read()); return c
def variants(it):
    s = {k: it[f] for k, f in (("nb", "summary"), ("nn", "summary_nn"), ("en", "summary_en")) if (it.get(f) or "").strip()}
    t = {k: it[f] for k, f in (("nn", "title_nn"), ("en", "title_en")) if it.get(f)}
    return s, t
def upsert(c, it, at, origin=None, ev="published"):
    s, t = variants(it); langs = sorted(s, key=["nn", "nb", "en"].index)
    row = c.execute("SELECT removed, summaries, first_published_on_site FROM articles WHERE site=? AND id=?", (SITE_ID, it["id"])).fetchone()
    if row is None:
        c.execute("""INSERT INTO articles (site,id,url,canonical_url,title,source,source_name,published_at,first_published_on_site,last_seen_on_site,languages,summaries,titles,topics,origin,updated_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (SITE_ID, it["id"], it["url"], canon(it["url"]), it["title"], it.get("source"), it.get("source_name"), it.get("published"), at, at,
                   json.dumps(langs), json.dumps(s, ensure_ascii=False), json.dumps(t, ensure_ascii=False), json.dumps(it.get("topics", [])), origin, now()))
        c.execute("INSERT INTO article_events (site,id,at,event) VALUES (?,?,?,?)", (SITE_ID, it["id"], at, ev)); return "ny"
    old = json.loads(row[1]); merged = {**old, **s}  # eldre språkvariantar blir verande om dei fell bort
    c.execute("""UPDATE articles SET url=?, canonical_url=?, title=?, source=?, source_name=?, published_at=COALESCE(?, published_at), last_seen_on_site=?,
                 languages=?, summaries=?, titles=?, topics=?, origin=COALESCE(?, origin), removed=0, updated_at=? WHERE site=? AND id=?""",
              (it["url"], canon(it["url"]), it["title"], it.get("source"), it.get("source_name"), it.get("published"), at,
               json.dumps(sorted(merged, key=["nn", "nb", "en"].index)), json.dumps(merged, ensure_ascii=False), json.dumps(t, ensure_ascii=False), json.dumps(it.get("topics", [])), origin, now(), SITE_ID, it["id"]))
    if row[0]: c.execute("INSERT INTO article_events (site,id,at,event) VALUES (?,?,?,?)", (SITE_ID, it["id"], at, "republished"))
    elif merged != old: c.execute("INSERT INTO article_events (site,id,at,event,detail) VALUES (?,?,?,?,?)", (SITE_ID, it["id"], at, "updated", "summaries"))
    return "oppdatert"
def mark_removed(c, live_ids, at, reason=None):
    n = 0
    for (aid,) in c.execute("SELECT id FROM articles WHERE site=? AND removed=0", (SITE_ID,)).fetchall():
        if aid not in live_ids:
            c.execute("UPDATE articles SET removed=1, removed_at=?, removal_reason=COALESCE(?, removal_reason), updated_at=? WHERE site=? AND id=?", (at, reason, now(), SITE_ID, aid))
            c.execute("INSERT INTO article_events (site,id,at,event,detail) VALUES (?,?,?,?,?)", (SITE_ID, aid, at, "removed", reason)); n += 1
    return n
def origins():
    try: return {i["id"]: i.get("origin") for i in json.load(open(P("data", "news.json"), encoding="utf-8"))["items"] if i.get("origin")}
    except FileNotFoundError: return {}
def reasons():
    try: return {i["id"]: i.get("reject_reason") for i in json.load(open(P("data", "news.json"), encoding="utf-8"))["items"] if i.get("reject_reason")}
    except FileNotFoundError: return {}
def record(path, at):
    items = json.load(open(path, encoding="utf-8"))["items"]; c = db(); o = origins(); r = reasons(); stats = {"ny": 0, "oppdatert": 0}
    for it in items: stats[upsert(c, it, at, o.get(it["id"]))] += 1
    live = {i["id"] for i in items}
    rem = mark_removed(c, live, at, None)
    for aid, why in r.items(): c.execute("UPDATE articles SET removal_reason=? WHERE site=? AND id=? AND removed=1 AND removal_reason IS NULL", (why, SITE_ID, aid))
    c.commit(); export(c); print(f"arkiv: {stats['ny']} nye, {stats['oppdatert']} oppdaterte, {rem} merkte som fjerna, totalt {c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]} rader")
def backfill():
    c = db(); repo = P(".publish")
    if os.path.isdir(os.path.join(repo, ".git")):
        log = subprocess.check_output(["git", "-C", repo, "log", "--reverse", "--format=%H %cI", "--", "data/news.json"], text=True).split("\n")
        for line in filter(None, log):
            sha, at = line.split(" ", 1)
            try: items = json.loads(subprocess.check_output(["git", "-C", repo, "show", f"{sha}:data/news.json"], text=True))["items"]
            except subprocess.CalledProcessError: continue
            at = dt.datetime.fromisoformat(at).astimezone(OSLO).isoformat(timespec="seconds")
            for it in items: upsert(c, it, at, None, "backfill")
            mark_removed(c, {i["id"] for i in items}, at, None)
            print(f"gh-pages {sha[:7]} {at}: {len(items)} saker")
    o = origins()
    for aid, org in o.items(): c.execute("UPDATE articles SET origin=COALESCE(origin, ?) WHERE site=? AND id=?", (org, SITE_ID, aid))
    for aid, why in reasons().items(): c.execute("UPDATE articles SET removal_reason=COALESCE(removal_reason, ?) WHERE site=? AND id=? AND removed=1", (why, SITE_ID, aid))
    c.commit(); export(c); print(f"arkiv etter tilbakefylling: {c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]} rader")
def export(c=None):
    c = c or db(); c.row_factory = sqlite3.Row
    rows = [dict(r) for r in c.execute("SELECT * FROM articles ORDER BY first_published_on_site, id")]
    for r in rows:
        for k in ("languages", "summaries", "titles", "topics"): r[k] = json.loads(r[k])
        r.pop("origin", None)  # intern merknad blir ikkje med i den offentlege repo-kopien
    ev = [dict(r) for r in c.execute("SELECT * FROM article_events ORDER BY seq")]
    json.dump({"schema": 1, "site": SITE_ID, "exported_at": now(), "articles": rows, "events": ev}, open(P("archive", "articles.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "record"
    if cmd == "record": record(P("site", "data", "news.json"), sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--at" else now())
    elif cmd == "backfill": backfill()
    elif cmd == "export": export(); print("eksportert")
