#!/usr/bin/env python3
"""Nyheitsinntak frå Nordic Crypto (standard frå 4. okt. 2026). Kryptonytt hentar og researchar ikkje lenger norske saker sjølv:
Nordic Crypto (/workspace/nordic-crypto) gjer innhentinga for alle nordiske land, og dette skriptet hentar dei norske sakene derifrå
(country == "NO") inn i Kryptonytt sitt format (data/news.json + queue/review.json). Idempotent: kan køyrast så ofte ein vil.

Kva blir kopiert (berre det Nordic Crypto allereie har):
  - tittel, URL, utgivar (source/source_name), dato, betalingsmur, tema (omsette til Kryptonytt sine)
  - feltet "nc": Nordic Crypto sin status/verifisering (pending | published | rejected, approved_by/at, reject_reason,
    summary_i18n_review), engelsk samandrag, nn/nb-omsetjing (berre når ho er laga frå gjeldande engelsk tekst), title_en,
    kjelder (seen_via) og eventuelle bilete MED lisens og kreditering (bilete utan lisens blir aldri kopierte)
  - teaser til state/teasers.json (berre lokalt arbeidsgrunnlag, blir aldri publisert) og kandidat-entitetar til køen
Kryptonytt-redaktøren godkjenner framleis kvar sak i queue/approved.json (summary/summary_nn/summary_en). Køraden får eit
ferdig utkast ("utkast_frå_nordic_crypto") som redaktøren les over; ingenting blir publisert automatisk.
Saker Nordic Crypto har avvist, blir importerte som status "rejected" (rejected_by "Nordic Crypto") og lista i
queue/review.json -> nc_rejected, slik at redaktøren kan overstyre ved å godkjenne dei i approved.json.
Kryptonytt sine eigne avgjerder (approved.json items/rejected) blir aldri endra.

  .venv/bin/python tools/import_nordic_crypto.py [--dry-run] [--days N] [--require-fresh] [--keep-nc-rejected-pending]
Stiar: KRYPTONYTT_DIR / NORDIC_CRYPTO_DIR (standard /workspace/kryptonytt og /workspace/nordic-crypto)."""
import argparse, datetime as dt, fcntl, importlib.util, json, os, re, sys
KN = os.environ.get("KRYPTONYTT_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NC = os.environ.get("NORDIC_CRYPTO_DIR", "/workspace/nordic-crypto")
NOW = dt.datetime.now(dt.timezone.utc)
TOPIC_NC_TO_KN = {"crypto": "krypto", "blockchain": "blokkjede", "regulation": "regulering", "companies": "selskaper", "bitcoin": "bitcoin"}
AIKI = re.compile(r"\b(AI|KI)\b")

def load(p, d):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError: return d
def save(p, d):
    t = p + ".import.tmp"
    with open(t, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1); f.write("\n")
    os.replace(t, p)
def kn_fetch():  # Kryptonytt sine eigne normaliseringar (same id-ar/duplikatsjekk som fetch.py)
    spec = importlib.util.spec_from_file_location("kn_fetch", os.path.join(KN, "fetch.py")); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m

def nc_freshness():
    """Når køyrde Nordic Crypto-innhentinga sist? (logs/nightly-YYYYMMDD.txt + data/news.json->updated)"""
    log = os.path.join(NC, "logs", dt.datetime.now().strftime("nightly-%Y%m%d.txt"))
    done = os.path.exists(log) and "awaiting editor:" in open(log, encoding="utf-8", errors="replace").read()
    upd = load(os.path.join(NC, "data", "news.json"), {}).get("updated")
    age_h = (NOW - dt.datetime.fromisoformat(upd)).total_seconds() / 3600 if upd else None
    return done, (dt.datetime.fromtimestamp(os.path.getmtime(log)).strftime("%H:%M") if os.path.exists(log) else None), age_h

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--days", type=int, default=14, help="importer nye saker publiserte dei siste N dagane (status/utkast blir oppdaterte for alle)")
    ap.add_argument("--require-fresh", action="store_true", help="avslutt med kode 3 dersom Nordic Crypto-innhentinga ikkje er ferdig i dag")
    ap.add_argument("--keep-nc-rejected-pending", action="store_true", help="saker Nordic Crypto har avvist, går til Kryptonytt-køen som pending i staden for rejected")
    a = ap.parse_args()
    done, at, age = nc_freshness()
    print(f"nordic crypto: nattinnhenting i dag {'ferdig kl. ' + at if done else 'IKKJE funnen/ferdig'}; data/news.json oppdatert for {age:.1f} t sidan" if age is not None else "nordic crypto: data/news.json manglar")
    if not done and a.require_fresh:
        print("åtvaring: Nordic Crypto har ikkje køyrt nattinnhentinga i dag – importerer likevel det som finst", file=sys.stderr)
    F = kn_fetch(); norm_url, norm_title, iid, strip = F.norm_url, F.norm_title, F.iid, F.strip_tracking
    lock = open("/tmp/crosssite-handoff.lock", "w"); fcntl.flock(lock, fcntl.LOCK_EX)   # same lås som tools/crosssite_handoff.py

    nc_news = load(os.path.join(NC, "data", "news.json"), {"items": []})
    nc_ap = load(os.path.join(NC, "queue", "approved.json"), {})
    nc_q = load(os.path.join(NC, "queue", "review.json"), {})
    nc_teasers = load(os.path.join(NC, "state", "teasers.json"), {})
    nc_apd = {norm_url(x["url"]): x for x in nc_ap.get("items", []) if x.get("url")}
    nc_rej = {norm_url(x["url"]): x.get("reason") for x in nc_ap.get("rejected", []) if x.get("url")}

    newsf, qf, tf = (os.path.join(KN, *p) for p in (("data", "news.json"), ("queue", "review.json"), ("state", "teasers.json")))
    news = load(newsf, {"items": []}); q = load(qf, {"items_needing_summary": [], "candidate_entities": []}); teasers = load(tf, {})
    kn_ap = load(os.path.join(KN, "queue", "approved.json"), {})
    kn_decided = {norm_url(x["url"]) for x in kn_ap.get("items", []) + kn_ap.get("rejected", []) if x.get("url")}
    kn_rej_titles = [x["title_contains"].lower() for x in kn_ap.get("rejected", []) if x.get("title_contains")]
    by_url = {norm_url(i["url"]): i for i in news["items"]}; by_title = {norm_title(i["title"]): i for i in news["items"]}
    cutoff = NOW - dt.timedelta(days=a.days)

    def nc_block(it):
        apx = nc_apd.get(norm_url(it["url"]), {})
        status = it.get("status")
        summ = (apx.get("summary") or it.get("summary") or "").strip() or None
        i18n = apx.get("summary_i18n") if apx else it.get("summary_i18n")
        if apx and apx.get("summary_i18n_source") and apx.get("summary_i18n_source") != apx.get("summary"): i18n = None  # utdatert omsetjing (NC-regel)
        b = {"id": it["id"], "status": status, "summary_en": summ if status == "published" else None,
             "summary_nn": (i18n or {}).get("nn") if status == "published" else None, "summary_nb": (i18n or {}).get("nb") if status == "published" else None,
             "summary_i18n_review": apx.get("summary_i18n_review") or it.get("summary_i18n_review"),
             "title_en": apx.get("title_en") or it.get("title_en"), "approved_by": it.get("approved_by") or apx.get("approved_by"),
             "approved_at": it.get("approved_at") or apx.get("approved_at"),
             "reject_reason": (it.get("reject_reason") or nc_rej.get(norm_url(it["url"]))) if status == "rejected" else None,
             "source": it.get("source"), "source_name": it.get("source_name"), "via": it.get("via"), "seen_via": it.get("seen_via", []),
             "fetched": it.get("fetched"), "origin": it.get("origin"), "synced_at": NOW.isoformat(timespec="seconds")}
        img = apx.get("image") or it.get("image")   # bilete berre med lisens + kreditering + kjeldeside
        if isinstance(img, dict) and img.get("license") and (img.get("author") or img.get("credit")) and (img.get("source_page") or img.get("license_url")):
            b["image"] = {k: img[k] for k in ("file", "url", "source_page", "author", "credit", "license", "license_url", "origin") if img.get(k)}
        return {k: v for k, v in b.items() if v not in (None, [], "")}
    def verification(b):
        s = b.get("status")
        if s == "published": return f"godkjend hos Nordic Crypto ({b.get('approved_by', 'redaktør')}, {str(b.get('approved_at', ''))[:10]}); omsetjing: {b.get('summary_i18n_review', 'ukjend')}"
        if s == "rejected": return f"avvist hos Nordic Crypto: {b.get('reject_reason') or 'utan grunn'}"
        return "ventar på Nordic Crypto-redaktøren"
    def kn_topics(it):
        t = {TOPIC_NC_TO_KN[x] for x in it.get("topics", []) if x in TOPIC_NC_TO_KN}
        return sorted(t | set(F.topics_of(f"{it['title']}. {nc_teasers.get(it['id'], '')}")) - ({"krypto"} if t - {"krypto"} else set())) or ["krypto"]

    added, enriched, flips = [], 0, []
    nc_no = [i for i in nc_news["items"] if i.get("country") == "NO"]
    idmap = {}
    for it in sorted(nc_no, key=lambda i: i["published"]):
        cu = norm_url(it["url"]); b = nc_block(it)
        ex = by_url.get(cu) or by_title.get(norm_title(it["title"]))
        if ex is None:
            kn_has_decision = cu in kn_decided or any(t in it["title"].lower() for t in kn_rej_titles)
            if dt.datetime.fromisoformat(it["published"]) < cutoff and not kn_has_decision: continue  # (har Kryptonytt alt avgjort saka, blir ho teken inn så apply_approvals finn ho)
            url = strip(it["url"])
            ex = {"id": iid(url), "url": url, "title": it["title"], "source": it.get("source"), "source_name": it.get("source_name") or it.get("source"),
                  "via": "nordic-crypto", "seen_via": ["nordic-crypto"], "published": it["published"], "fetched": it.get("fetched") or NOW.isoformat(timespec="seconds"),
                  "imported": NOW.isoformat(timespec="seconds"), "topics": kn_topics(it), "matched": it.get("matched", []), "paywall": bool(it.get("paywall")),
                  "status": "pending", "summary": None, "origin": "henta frå Nordic Crypto"}
            news["items"].append(ex); by_url[cu] = ex; by_title[norm_title(ex["title"])] = ex; added.append(ex)
            if nc_teasers.get(it["id"]) and ex["id"] not in teasers: teasers[ex["id"]] = nc_teasers[it["id"]][:600]
        else:
            enriched += 1
            if "nordic-crypto" not in ex.setdefault("seen_via", []): ex["seen_via"].append("nordic-crypto")
            if not ex.get("paywall") and it.get("paywall"): ex["paywall"] = True
            if nc_teasers.get(it["id"]) and not teasers.get(ex["id"]): teasers[ex["id"]] = nc_teasers[it["id"]][:600]
        ex["nc"] = b; ex["nc_verification"] = verification(b); idmap[it["id"]] = ex["id"]
        # Status: Kryptonytt sine eigne avgjerder vinn alltid. Utan Kryptonytt-avgjerd følgjer køen Nordic Crypto sin avvising.
        if norm_url(ex["url"]) in kn_decided or any(t in ex["title"].lower() for t in kn_rej_titles) or ex.get("status") == "published": continue
        if b["status"] == "rejected" and not a.keep_nc_rejected_pending and ex.get("status") == "pending":
            ex.update(status="rejected", rejected_by="Nordic Crypto", reject_reason=f"Avvist hos Nordic Crypto: {b.get('reject_reason') or 'utan grunn'}"); flips.append(("rejected", ex))
        elif b["status"] != "rejected" and ex.get("rejected_by") == "Nordic Crypto":
            ex["status"] = "pending"; ex.pop("rejected_by", None); ex.pop("reject_reason", None); flips.append(("pending", ex))

    # Kø: saker som ventar på Kryptonytt-redaktøren, med utkast frå Nordic Crypto
    items = {i["id"]: i for i in news["items"]}
    rows = {r["id"]: r for r in q.get("items_needing_summary", [])}
    for i in news["items"]:
        if i.get("status") == "pending" and i["id"] not in rows:
            rows[i["id"]] = {"id": i["id"], "title": i["title"], "source": i["source_name"], "url": i["url"], "published": i["published"],
                             "teaser_local_only": teasers.get(i["id"], "")}
    for rid, r in rows.items():
        i = items.get(rid)
        if not i or not i.get("nc"): continue
        b = i["nc"]; r["origin"] = i.get("origin") or r.get("origin") or "henta frå Nordic Crypto"; r["nc_verification"] = i["nc_verification"]
        r["nc_sources"] = {"source_name": b.get("source_name"), "seen_via": b.get("seen_via", [])}
        if b.get("image"): r["nc_image"] = b["image"]
        if b.get("summary_en"):
            d = {"url": i["url"], "summary": b.get("summary_nb"), "summary_nn": b.get("summary_nn"), "summary_en": b["summary_en"], "topics": i.get("topics"),
                 "_merk": "Utkast frå Nordic Crypto (engelsk samandrag + nn/nb-omsetjing). Les over, rett og legg i queue/approved.json -> items; "
                          "approved_by/approved_at set du sjølv. Eksterne titlar blir ståande som i kjelda."}
            bad = [k for k in ("summary", "summary_nn") if AIKI.search(d.get(k) or "")]
            if bad: d["_språkregel"] = f"{', '.join(bad)} inneheld «AI»/«KI» – skriv «kunstig intelligens»"
            r["utkast_frå_nordic_crypto"] = {k: v for k, v in d.items() if v}
        else: r.pop("utkast_frå_nordic_crypto", None)
        if not r.get("teaser_local_only") and teasers.get(rid): r["teaser_local_only"] = teasers[rid]
    q["items_needing_summary"] = [r for r in rows.values() if items.get(r["id"], {}).get("status") == "pending"]
    q["nc_rejected"] = [{"id": i["id"], "title": i["title"], "url": i["url"], "published": i["published"], "reason": i.get("reject_reason")}
                        for i in news["items"] if i.get("rejected_by") == "Nordic Crypto" and i.get("status") == "rejected"]
    q["_nc_how_to"] = ("Norske saker kjem frå Nordic Crypto (tools/import_nordic_crypto.py). nc_verification viser status der. "
                       "nc_rejected: avviste hos Nordic Crypto – vil du likevel ha ei sak, legg ho i queue/approved.json -> items som vanleg.")
    # kandidat-entitetar frå Nordic Crypto for dei importerte sakene
    org = load(os.path.join(KN, "data", "orgchart.json"), {"entities": []})
    known = {e["name"].lower() for e in org.get("entities", [])} | {n.lower() for n in load(os.path.join(KN, "state", "rejected_candidates.json"), [])}
    seen = {(c["name"].lower(), c.get("item_id")) for c in q.get("candidate_entities", [])}
    new_ids = {x["id"] for x in added}; n_cand = 0
    for c in nc_q.get("candidate_entities", []):
        kid = idmap.get(c.get("item_id"))
        if kid not in new_ids or c["name"].lower() in known or (c["name"].lower(), kid) in seen: continue
        n = {k: v for k, v in c.items() if k not in ("country", "item_id", "status")}
        n.update(kind={"organisation": "organisasjon"}.get(c.get("kind"), c.get("kind")), item_id=kid, status="new", origin="Nordic Crypto")
        q.setdefault("candidate_entities", []).append(n); seen.add((c["name"].lower(), kid)); n_cand += 1
    q["updated"] = NOW.isoformat(timespec="seconds")
    news["items"].sort(key=lambda i: i["published"], reverse=True); news["updated"] = NOW.isoformat(timespec="seconds")
    if not a.dry_run:
        save(newsf, news); save(qf, q); save(tf, teasers)
    today = dt.datetime.now().date()
    print(f"import frå Nordic Crypto{' (dry-run)' if a.dry_run else ''}: {len(nc_no)} norske saker der, {len(added)} nye her "
          f"({sum(x['status']=='pending' for x in added)} til redaktøren, {sum(x['status']=='rejected' for x in added)} avviste hos Nordic Crypto), "
          f"{enriched} fanst frå før (status/utkast oppdatert), {len(flips)} statusendringar, {n_cand} kandidat-entitetar; "
          f"{len(q['items_needing_summary'])} ventar på oppsummering")
    for x in added: print(f"   + {x['published'][:10]} [{x['status']}] {x['source_name']}: {x['title'][:80]}  ({x['nc_verification']})")
    for s, x in flips: print(f"   ~ {s}: {x['title'][:80]}")
    tod = [i for i in nc_no if (i.get("fetched") or "")[:10] == today.isoformat() or i["published"][:10] == today.isoformat()]
    for i in tod:
        k = by_url.get(norm_url(i["url"]))
        print(f"   i dag: {i['published'][:16]} {i.get('source_name')}: {i['title'][:70]} -> Kryptonytt {k['id'] if k else '–'} [{k.get('status') if k else 'ikkje importert'}]")
    if not done and a.require_fresh: sys.exit(3)

if __name__ == "__main__": main()
