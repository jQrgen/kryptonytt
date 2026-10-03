"""Kalender (med «Tidlegare arrangement»), endringslogg og Akademia, på tre språk. Kallast frå build.py via site_pages."""
import json, os, re, calendar, datetime as dt
import build as B
from build import L, tr, E, P, S, load, page, nodate, OSLO
GH = '<a href="https://github.com/jQrgen/kryptonytt/issues" rel="noopener">GitHub</a>'
MND = {"nn": ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"],
       "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
MND["nb"] = MND["nn"]
UKEDAG = {"nn": ["mån", "tys", "ons", "tor", "fre", "lau", "søn"], "nb": ["man", "tir", "ons", "tor", "fre", "lør", "søn"], "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}

def events_for_site():
    """data/events.json + redaktøren sine val i queue/approved.json -> events (approve/reject/notes[_nn/_en]/sponsored/paid)."""
    ev = load(P("data", "events.json"), {"events": []}); ap = (load(P("queue", "approved.json"), {}) or {}).get("events", {})
    now = dt.datetime.now(OSLO); out = []
    for e in ev["events"]:
        e = dict(e)
        if e["id"] in ap.get("reject", []): continue
        if e["id"] in ap.get("approve", []): e["status"] = "published"
        if e["status"] != "published": continue
        if not (e.get("place") or e.get("online")) or not e.get("organiser") or not e.get("start"): continue  # regel: dato, stad og arrangør
        e["note"] = ap.get("notes", {}).get(e["id"])
        for lg in ("nn", "en"): e[f"note_{lg}"] = ap.get(f"notes_{lg}", {}).get(e["id"])
        if e["id"] in ap.get("sponsored", []): e["sponsored"] = True
        if e["id"] in ap.get("paid", {}): e["paid"] = ap["paid"][e["id"]]
        out.append({k: e.get(k) for k in ("id", "title", "start", "end", "place", "city", "online", "organiser", "url", "source", "paid", "sponsored", "note", "note_nn", "note_en")})
    # Arkiv (spora i git): alle arrangement som nokon gong er godkjende. Regel frå jQrgen: avslutta arrangement blir ALDRI sletta,
    # dei blir flytte til «Tidlegare arrangement». Henting og bygging kan berre leggje til eller oppdatere, aldri fjerne.
    arkf = P("arkiv", "arrangementer.json"); ark = load(arkf, {"events": []}); by = {e["id"]: e for e in ark["events"]}
    for e in out: by[e["id"]] = {k: v for k, v in e.items() if not (k in ("note_nn", "note_en") and v is None)}
    ark["events"] = sorted(by.values(), key=lambda e: e["start"])
    os.makedirs(os.path.dirname(arkf), exist_ok=True)
    json.dump(ark, open(arkf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    res = []
    for e in ark["events"]:
        if e["id"] in ap.get("reject", []): continue  # skjult om redaktøren trekkjer han tilbake, men ligg framleis i arkivet
        e = dict(e); e["past"] = dt.datetime.fromisoformat(e.get("end") or e["start"]) < now; res.append(e)
    return sorted(res, key=lambda e: e["start"]), now

def build_changelog():
    log = load(P("endringer.json"), {"entries": []}); apf = P("queue", "approved.json"); ap = load(apf, {}) or {}
    flags = {"akademia": B.AKADEMIA_ON and bool((ap.get("akademia") or {}).get("enabled")), "reglar": B.REGEL_ON and bool((ap.get("reglar") or {}).get("enabled"))}
    out = []
    for e in log["entries"]:
        f = e.get("feature")
        if f:
            if not flags.get(f): continue
            cfgf = ap.setdefault(f, {})
            if not cfgf.get("live_date"):  # første bygg der funksjonen er på = dagen han går live
                cfgf["live_date"] = dt.datetime.now(OSLO).date().isoformat()
                json.dump(ap, open(apf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            e = dict(e, date=cfgf["live_date"])
        if e.get("date"): out.append(e)
    out.sort(key=lambda e: e["date"], reverse=True)
    lis = "".join(f'<li><time datetime="{E(e["date"])}"><b>{nodate(e["date"] + "T12:00:00+02:00")}</b></time><p class="sum"{tr(e, "text")[1]}>{E(tr(e, "text")[0])}</p></li>' for e in out)
    body = f"""<h1>{L("Endringslogg", "Endringslogg", "Changelog")}</h1>
<p class="lead">{L("Endringar på Kryptonytt Norge: nye sider, seksjonar og funksjonar. Nyaste først. Daglege nyheiter står ikkje her.", "Endringer på Kryptonytt Norge: nye sider, seksjoner og funksjoner. Nyeste først. Daglige nyheter står ikke her.", "Changes to Kryptonytt Norge: new pages, sections and features. Newest first. Daily news is not listed here.")}</p>
<ol class="news">{lis or '<li class="empty">' + L("Ingen endringar enno.", "Ingen endringer ennå.", "No changes yet.") + '</li>'}</ol>
<p class="meta">{L("Kjeldekoden og heile historikken ligg på", "Kildekoden og hele historikken ligger på", "The source code and full history are on")} <a href="https://github.com/jQrgen/kryptonytt/commits/main" rel="noopener">GitHub</a>.</p>"""
    page("endringer", L("Endringslogg – Kryptonytt Norge", "Endringslogg – Kryptonytt Norge", "Changelog – Kryptonytt Norge"), "endringer", body,
         L("Endringslogg for Kryptonytt Norge: nye sider, seksjonar og funksjonar.", "Endringslogg for Kryptonytt Norge: nye sider, seksjoner og funksjoner.", "Changelog for Kryptonytt Norge: new pages, sections and features."))
    if S.lang == "nn": print(f"endringslogg: {len(out)} oppføringar")

def build_akademia():
    a = load(P("data", "akademia.json"), {})
    G = {k: [r for r in a.get(k, []) if r.get("status") == "godkjent"] for k in ("courses", "groups", "publications", "research")}  # berre redaktørgodkjende rader
    NB = "" if S.lang == "nb" else ' lang="nb"'
    def lk(u, t): return f'<a href="{E(u)}" rel="noopener" target="_blank">{E(t)}</a>' if u else E(t)
    def ver(r):
        v = r.get("verification") or ""
        if v.startswith("🟡"): return f'<div class="meta"><span class="tag pw">{L("delvis stadfesta", "delvis bekreftet", "partly confirmed")}</span> <span{NB}>{E(re.sub(r"^🟡\s*delvis bekreftet\s*", "", v).strip(" ()"))}</span></div>'
        return ""
    def chk(r): return f'{L("Sjekka", "Sjekket", "Checked")} {E(r.get("checked") or "")}'
    act = {"aktiv": L("aktiv", "aktiv", "active"), "inaktiv": L("inaktiv", "inaktiv", "inactive")}
    rows = "".join(f'<tr><td><b>{E(r.get("code") or "")}</b></td><td>{lk(r.get("url"), r.get("name") or "")}<div class="meta"{NB}>{E(r.get("about") or "")}</div>{ver(r)}</td>'
                   f'<td>{E(r.get("institution") or "")}</td><td{NB}>{E(r.get("level") or "")}</td><td{NB}>{E(r.get("offered") or "")}</td><td class="meta">{chk(r)}</td></tr>' for r in G["courses"])
    grp = "".join(f'<li><h3>{lk(r.get("url"), r.get("name") or "")} <span class="tag">{E(act.get(r.get("activity") or "inaktiv", r.get("activity")))}</span></h3>'
                  f'<div class="meta">{E(r.get("institution") or "")} · {L("Siste dokumenterte aktivitet", "Siste dokumenterte aktivitet", "Last documented activity")}: {E(r.get("last_activity") or L("ukjend", "ukjent", "unknown"))} · {chk(r)}</div>{ver(r)}</li>' for r in G["groups"])
    def doi(r):
        d = r.get("doi") or ""; x = lk(r.get("url"), "DOI " + d) if d else ""
        return x + (" · " + lk(r["nva"], "NVA/Cristin") if r.get("nva") else "")
    pubs = "".join(f'<li><h3>{lk(r.get("url"), r.get("title") or "")}</h3><div class="meta">{E(", ".join(r.get("authors") or []))} · {E(str(r.get("year") or ""))}'
                   f'{(" · <i>" + E(r["venue"]) + "</i>") if r.get("venue") else ""}</div><div class="meta">{L("Norsk institusjon", "Norsk institusjon", "Norwegian institution")}: {E(r.get("institution") or "")} · {doi(r)} · {chk(r)}</div>{ver(r)}</li>' for r in G["publications"])
    res = "".join(f'<li><h3>{lk(r.get("url"), r.get("name") or "")}</h3><div class="meta">{E(r.get("institution") or "")}{(" · <span" + NB + ">" + E(r["funding"]) + "</span>") if r.get("funding") else ""}{(" · " + E(r["period"])) if r.get("period") else ""} · {chk(r)}</div>'
                  f'<p class="sum"{NB}>{E(r.get("about") or "")}</p>{ver(r)}</li>' for r in G["research"])
    n = {k: len(v) for k, v in G.items()}
    upd = E(a.get("updated") or "")
    body = L(
f"""<h1>Akademia: blokkjede og krypto ved norske universitet og høgskular</h1>
<p class="lead">Emne, studentinitiativ, forsking og publikasjonar om blokkjede, bitcoin og kryptovaluta i norsk akademia. Kvar rad har lenkje til kjelda og dato for når vi sjekka ho. Oversikta er laga med hjelp av kunstig intelligens og gjennomgått av redaksjonen{(" (kartlagd per " + upd + ")") if upd else ""}. Skildringane frå researcharbeidet står på bokmål.</p>
<p class="notice">Vi tek med eit emne berre når blokkjede eller krypto er ein vesentleg del av pensum ifølgje emnesida. Publikasjonar har DOI- eller NVA/Cristin-lenkje. Studentgrupper blir merkte «aktiv» berre med datert aktivitet dei siste 12 månadene. Utvalet er representativt, ikkje fullstendig. Manglar noko? Send det som ei sak på {GH}.</p>""",
f"""<h1>Akademia: blokkjede og krypto ved norske universiteter og høyskoler</h1>
<p class="lead">Emner, studentinitiativer, forskning og publikasjoner om blokkjede, bitcoin og kryptovaluta i norsk akademia. Hver rad har lenke til kilden og dato for når vi sjekket den. Oversikten er laget med hjelp av kunstig intelligens og gjennomgått av redaksjonen{(" (kartlagt per " + upd + ")") if upd else ""}.</p>
<p class="notice">Vi tar med et emne bare når blokkjede eller krypto er en vesentlig del av pensum ifølge emnesiden. Publikasjoner har DOI- eller NVA/Cristin-lenke. Studentgrupper merkes «aktiv» bare med datert aktivitet de siste 12 månedene. Utvalget er representativt, ikke fullstendig. Mangler noe? Send det som en sak på {GH}.</p>""",
f"""<h1>Academia: blockchain and crypto at Norwegian universities and university colleges</h1>
<p class="lead">Courses, student initiatives, research and publications on blockchain, bitcoin and cryptocurrency in Norwegian academia. Every row links to its source and shows when we checked it. The overview was made with help from artificial intelligence and reviewed by our editors{(" (as of " + upd + ")") if upd else ""}. Course descriptions and notes from our research are in Norwegian.</p>
<p class="notice">We include a course only when blockchain or crypto is a substantial part of the syllabus according to the course page. Publications have a DOI or NVA/Cristin link. Student groups are marked “active” only with dated activity in the past 12 months. The selection is representative, not complete. Missing something? Send it as an issue on {GH}.</p>""")
    body += f"""
<nav class="meta" aria-label="{L("Seksjonar", "Seksjoner", "Sections")}"><a href="#emner">{L("Emne", "Emner", "Courses")} ({n["courses"]})</a> · <a href="#studenter">{L("Linjeforeiningar og studentinitiativ", "Linjeforeninger og studentinitiativer", "Student associations and initiatives")} ({n["groups"]})</a> · <a href="#publikasjoner">{L("Publikasjonar", "Publikasjoner", "Publications")} ({n["publications"]})</a> · <a href="#forskning">{L("Forskingsmiljø og prosjekt", "Forskningsmiljøer og prosjekter", "Research groups and projects")} ({n["research"]})</a></nav>
<h2 id="emner">{L("Emne og studieprogram", "Emner og studieprogrammer", "Courses and study programmes")}</h2>
<table class="list"><thead><tr><th>{L("Emnekode", "Emnekode", "Course code")}</th><th>{L("Emne", "Emne", "Course")}</th><th>Institusjon</th><th>{L("Studiepoeng / nivå", "Studiepoeng / nivå", "Credits / level")}</th><th>{L("Blir tilbode", "Tilbys", "Offered")}</th><th>{L("Sjekka", "Sjekket", "Checked")}</th></tr></thead><tbody>{rows or '<tr><td colspan=6>' + L("Ingen godkjende emne enno.", "Ingen godkjente emner ennå.", "No approved courses yet.") + '</td></tr>'}</tbody></table>
<h2 id="studenter">{L("Linjeforeiningar og studentinitiativ", "Linjeforeninger og studentinitiativer", "Student associations and initiatives")}</h2><ol class="news">{grp or '<li class="empty">' + L(f"Vi har ikkje funne nokon aktiv linjeforeining eller studentforeining for blokkjede eller krypto med dokumentert aktivitet dei siste 12 månadene. Kjenner du til ei? Send oss ei lenkje på {GH}.", f"Vi har ikke funnet noen aktiv linjeforening eller studentforening for blokkjede eller krypto med dokumentert aktivitet de siste 12 månedene. Kjenner du til en? Send oss en lenke på {GH}.", f"We have not found any active student association for blockchain or crypto with documented activity in the past 12 months. Know of one? Send us a link on {GH}.") + '</li>'}</ol>
<h2 id="publikasjoner">{L("Akademiske publikasjonar", "Akademiske publikasjoner", "Academic publications")}</h2><ol class="news">{pubs or '<li class="empty">' + L("Ingen godkjende publikasjonar enno.", "Ingen godkjente publikasjoner ennå.", "No approved publications yet.") + '</li>'}</ol>
<h2 id="forskning">{L("Forskingsmiljø og prosjekt", "Forskningsmiljøer og prosjekter", "Research groups and projects")}</h2><ol class="news">{res or '<li class="empty">' + L("Ingen godkjende oppføringar enno.", "Ingen godkjente oppføringer ennå.", "No approved entries yet.") + '</li>'}</ol>"""
    if S.lang == "en": body = body.replace("<th>Institusjon</th>", "<th>Institution</th>")
    page("akademia", L("Akademia – blokkjede og krypto i norsk akademia", "Akademia – blokkjede og krypto i norsk akademia", "Academia – blockchain and crypto in Norwegian academia"), "akademia", body,
         L("Emne, studentinitiativ, publikasjonar og forskingsmiljø om blokkjede og krypto ved norske universitet og høgskular.", "Emner, studentinitiativer, publikasjoner og forskningsmiljøer om blokkjede og krypto ved norske universiteter og høyskoler.", "Courses, student initiatives, publications and research groups on blockchain and crypto at Norwegian universities and university colleges."))
    if S.lang == "nn": print("akademia-side: " + ", ".join(f"{k}={v}" for k, v in n.items()))

def build_calendar(ctx):
    evs, now, cfg = ctx["evs"], ctx["now"], ctx["cfg"]
    up = [e for e in evs if not e["past"]]; past = [e for e in evs if e["past"]][::-1]  # alle tidlegare, nyaste først
    M, W = MND[S.lang], UKEDAG[S.lang]
    def when(e):
        a = dt.datetime.fromisoformat(e["start"]); b = dt.datetime.fromisoformat(e["end"]) if e.get("end") else None
        if S.lang == "en":
            t = f'{W[a.weekday()]} {a.day} {M[a.month-1]} {a.year}, {a:%H:%M}'
            return t + (f'–{b:%H:%M}' if b and b.date() == a.date() else (f' – {b.day} {M[b.month-1]}' if b else ""))
        t = f'{W[a.weekday()]} {a.day}. {M[a.month-1]} {a.year} kl. {a:%H.%M}'
        return t + (f'–{b:%H.%M}' if b and b.date() == a.date() else (f' – {b.day}. {M[b.month-1]}' if b else ""))
    def badges(e):
        b = []
        if e.get("paid"): b.append('<span class="tag pw">' + L("Betalt", "Betalt", "Paid") + '</span>')
        elif e.get("paid") is False: b.append('<span class="tag">' + L("Gratis", "Gratis", "Free") + '</span>')
        if e.get("sponsored"): b.append('<span class="tag pw">' + L("Sponsa", "Sponset", "Sponsored") + '</span>')
        if e.get("online"): b.append('<span class="tag">' + L("Digitalt", "Digitalt", "Online") + '</span>')
        return " ".join(b)
    def li(e):
        note, nl = tr(e, "note")
        return (f'<li id="e-{E(e["id"])}"><h3><a href="{E(e["url"])}" rel="noopener" target="_blank">{E(e["title"])}</a></h3>'
                f'<div class="meta"><time datetime="{E(e["start"])}"><b>{E(when(e))}</b></time> · {E(e.get("place") or L("Digitalt", "Digitalt", "Online"))} {badges(e)}</div>'
                f'<div class="meta">{L("Arrangør", "Arrangør", "Organiser")}: {E(e["organiser"])} · {L("Kjelde", "Kilde", "Source")}: <a href="{E(e["url"])}" rel="noopener" target="_blank">{E(e["source"])}</a></div>'
                + (f'<p class="sum"><b>{L("Merk", "Merk", "Note")}:</b> <span{nl}>{E(note)}</span></p>' if note else "") + '</li>')
    months = sorted({(now.year, now.month)} | {(int(e["start"][:4]), int(e["start"][5:7])) for e in up})
    grids = []
    for y, m in months:
        cells = []
        for wk in calendar.Calendar(0).monthdatescalendar(y, m):
            row = []
            for d in wk:
                de = [e for e in up if e["start"][:10] == d.isoformat()]
                cls = " ".join(c for c in ["out" if d.month != m else "", "today" if d == now.date() else "", "has" if de else ""] if c)
                row.append(f'<td class="{cls}"><span class="d">{d.day}</span>' + "".join(f'<a href="#e-{E(e["id"])}">{E(e["title"])}</a>' for e in de) + '</td>')
            cells.append("<tr>" + "".join(row) + "</tr>")
        grids.append(f'<table class="cal"><caption>{M[m-1].capitalize()} {y}</caption><thead><tr>{"".join(f"<th>{d}</th>" for d in W)}</tr></thead><tbody>{"".join(cells)}</tbody></table>')
    NB = "" if S.lang == "nb" else ' lang="nb"'
    esrc = "".join(f'<li><a href="{E(s["url"])}" rel="noopener" target="_blank">{E(s["name"])}</a> – <span{NB}>{E(s.get("status", ""))}</span></li>' for s in cfg.get("event_sources", []) if s.get("enabled"))
    body = L(
"""<h1>Kalender: krypto, bitcoin og blokkjede i Noreg</h1>
<p class="lead">Komande arrangement, møte og føredrag. Vi tek berre med arrangement der arrangøren si eiga side eller ei offentleg oppføring viser dato, stad og arrangør, og som faktisk handlar om krypto, bitcoin eller blokkjede. Betalte og sponsa arrangement er merkte. Sjekk alltid detaljane hos arrangøren.</p>""",
"""<h1>Kalender: krypto, bitcoin og blokkjede i Norge</h1>
<p class="lead">Kommende arrangementer, møter og foredrag. Vi tar bare med arrangementer der arrangørens egen side eller en offentlig oppføring viser dato, sted og arrangør, og som faktisk handler om krypto, bitcoin eller blokkjede. Betalte og sponsede arrangementer er merket. Sjekk alltid detaljene hos arrangøren.</p>""",
"""<h1>Calendar: crypto, bitcoin and blockchain in Norway</h1>
<p class="lead">Upcoming events, meetups and talks. We only include events where the organiser’s own page or a public listing shows the date, place and organiser, and that are genuinely about crypto, bitcoin or blockchain. Paid and sponsored events are labelled. Event titles are shown as the organiser wrote them. Always check the details with the organiser.</p>""")
    body += f"""
<div class="calgrid">{''.join(grids)}</div>
<h2>{L("Komande", "Kommende", "Upcoming")}</h2><ol class="news">{''.join(li(e) for e in up) or '<li class="empty">' + L("Ingen komande arrangement registrerte.", "Ingen kommende arrangementer registrert.", "No upcoming events registered.") + '</li>'}</ol>
<h2 id="tidligere">{L("Tidlegare arrangement", "Tidligere arrangementer", "Past events")}</h2><p class="meta">{L("Arrangement blir flytte hit automatisk når dei er over (norsk tid). Vi slettar dei ikkje.", "Arrangementer flyttes hit automatisk når de er over (norsk tid). Vi sletter dem ikke.", "Events move here automatically once they are over (Norwegian time). We never delete them.")}</p><ol class="news past">{''.join(li(e) for e in past) or '<li class="empty">' + L("Ingen tidlegare arrangement enno.", "Ingen tidligere arrangementer ennå.", "No past events yet.") + '</li>'}</ol>
<h2>{L("Kvar vi finn arrangement", "Hvor vi finner arrangementer", "Where we find events")}</h2><ul class="prose">{esrc}</ul>
<p class="meta">{L(f"Arrangerer du noko om krypto i Noreg? Send lenkje til arrangørsida som ei sak på {GH}.", f"Arrangerer du noe om krypto i Norge? Send lenke til arrangørsiden som en sak på {GH}.", f"Organising something about crypto in Norway? Send a link to the organiser’s page as an issue on {GH}.")}</p>"""
    page("kalender", L("Kalender – krypto, bitcoin og blokkjede i Noreg", "Kalender – krypto, bitcoin og blokkjede i Norge", "Calendar – crypto, bitcoin and blockchain in Norway"), "kalender", body,
         L("Komande arrangement om krypto, bitcoin og blokkjede i Noreg, med dato, stad og arrangør.", "Kommende arrangementer om krypto, bitcoin og blokkjede i Norge, med dato, sted og arrangør.", "Upcoming events about crypto, bitcoin and blockchain in Norway, with date, place and organiser."))
    if S.lang == "nn": print(f"kalender: {len(up)} komande, {len(past)} tidlegare")
