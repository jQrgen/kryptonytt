#!/usr/bin/env python3
"""Engangs-seed for data/akademia.json (egen research 03.10.2026). Alle rader: status «venter på redaktør».
Publikasjonsmetadata hentes fra OpenAlex via DOI (ingenting skrives for hånd)."""
import json, os, requests
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "KryptonyttNorge/1.0 (https://jqrgen.github.io/kryptonytt/)"}
C = "2026-10-03"; ST = "venter på redaktør"
courses = [
 ("TTM4195", "Blokkjede-teknologier og kryptografiske verktøy", "NTNU", "Master, 7,5 sp, høst", "https://www.ntnu.no/studier/emner/TTM4195", "Kryptografien bak Bitcoin og andre kryptovalutaer, design av kryptovaluta, smartkontrakter."),
 ("IN5420", "Distributed Blockchain Technologies", "Universitetet i Oslo", "Master, 10 sp, vår", "https://www.uio.no/studier/emner/matnat/ifi/IN5420/", "Forskningsseminar om bitcoin, blokkjedelagring, konsensusprotokoller, sikkerhet og personvern."),
 ("IN9420", "Distributed Blockchain Technologies", "Universitetet i Oslo", "Ph.d., 10 sp, vår", "https://www.uio.no/studier/emner/matnat/ifi/IN9420/index.html", "Ph.d.-varianten av IN5420."),
 ("INFO384", "Blokkjede-teknologi og formelle metoder", "Universitetet i Bergen", "Master, 15 sp", "https://www4.uib.no/studier/emner/info384", "Blokkjedeteori, konsensus (PoW/PoS) analysert med formelle metoder, smartkontrakter i Solidity."),
 ("INFO384B", "Blokkjede-teknologi", "Universitetet i Bergen", "Master, 10 sp, høst", "https://www4.uib.no/studier/emner/info384b", "Blokkjedeteori og -modeller, konsensus, Ethereum-smartkontrakter og kryptografi."),
 ("IKT519", "Blokkjeder og distribuerte teknologier", "Universitetet i Agder", "Master, 7,5 sp", "https://www.uia.no/studier/emner/2027/var/ikt519.html", "Kryptografi i blokkjeder, Bitcoin-konsensus, -skript, -utvinning og -anonymitet, altcoins."),
 ("FOR20", "Introduction to Blockchain", "NHH", "Bachelor (BA Economics and Business Administration)", "https://www.nhh.no/en/courses/introduction-to-blockchain/", "Hva en blokkjede er, konsensusprotokoller, smartkontrakter, digitalisering av eiendeler og DeFi."),
 ("LUS2030", "Blokkjeder, kryptovaluta og digitale sentralbankpenger", "Handelshøyskolen BI", "Videreutdanning (modul i «Digital transformasjon i finansnæringen»)", "https://www.bi.no/studier-og-kurs/videreutdanning/kompetanseheving-bransjeprogram/digital-transformasjon-i-finansnaringen/", "Bitcoin og blokkjedeteknologi, alternative kryptovalutaer, digitale sentralbankpenger, DeFi, NFT og Web3."),
]
groups = [
 ("BISO Web3 Society", "Handelshøyskolen BI (BISO Oslo)", "inaktiv", "Siste daterte aktivitet vi fant: gjesteforelesninger og et arrangement med Kaupr i november 2024 (over 12 måneder siden).", "https://www.kaupr.io/en/news/the-web3-society-at-bi-is-ramping-up-its-activities"),
 ("Blockwave Norway", "Universitetet i Oslo (studentinitiativ)", "inaktiv", "Studentorganisasjon for blokkjede startet av en UiO-student, omtalt i Titan.uio.no i mai 2019. Ingen nyere datert aktivitet funnet.", "https://www.titan.uio.no/utdanning/2019/blockchain-er-faget-der-studentene-er-laerere.html"),
]
research = [
 ("Blockchain-UiO", "Universitetet i Oslo, Institutt for informatikk", "Akademisk-industrielt laboratorium for blokkjedeteknologi: forskning, emner, masteroppgaver og samarbeid med næringslivet.", "https://www.mn.uio.no/ifi/english/research/networks/blockchainlab/index.html"),
 ("Decentralised Systems Engineering Lab", "NTNU, Institutt for datateknologi og informatikk", "Forsker blant annet på personvern og anonymitet i kryptovalutaer, kryptovalutaanalyse for politiet, konsensus, DeFi og Lightning.", "https://www.ntnu.edu/idi/dse"),
 ("Trust and Transparency in Digital Society Through Blockchain Technology", "NTNU Digital Transformation", "Tverrfaglig prosjekt med seks delprosjekter: kryptografi, nettverk, identitet, verdikjeder, helse og organisasjon.", "https://www.ntnu.edu/digital-transformation/blockchain"),
]
dois = ["10.1016/j.giq.2017.09.007", "10.1016/j.frl.2018.08.010", "10.1016/j.jebo.2020.05.005", "10.1007/s11187-019-00286-y",
        "10.1016/j.ijforecast.2018.09.005", "10.1016/j.ijmedinf.2019.104040", "10.1016/j.frl.2021.102031",
        "10.1016/j.techfore.2022.121739", "10.1016/j.frl.2016.09.025"]
pubs = []
for d in dois:
    w = requests.get(f"https://api.openalex.org/works/doi:{d}", headers=UA, timeout=30).json()
    au = [a["author"]["display_name"] for a in w["authorships"]]
    no = []
    for a in w["authorships"]:
        for i in a["institutions"]:
            if i.get("country_code") == "NO" and i["display_name"] not in no: no.append(i["display_name"])
    pubs.append({"title": w["title"], "authors": au, "institution": ", ".join(no), "year": w["publication_year"],
                 "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"), "doi": d, "url": f"https://doi.org/{d}",
                 "source": f"https://doi.org/{d}", "checked": C, "status": ST, "origin": "seed"})
out = {"updated": C, "note": "Seed fra egen research; erstattes/utvides av research/akademia.md når redaktøren har godkjent den.",
 "courses": [{"code": a, "name": b, "institution": c, "level": d, "url": e, "about": f, "source": e, "checked": C, "status": ST, "origin": "seed"} for a, b, c, d, e, f in courses],
 "groups": [{"name": a, "institution": b, "activity": c, "about": d, "url": e, "source": e, "checked": C, "status": ST, "origin": "seed"} for a, b, c, d, e in groups],
 "publications": pubs,
 "research": [{"name": a, "institution": b, "about": c, "url": d, "source": d, "checked": C, "status": ST, "origin": "seed"} for a, b, c, d in research]}
json.dump(out, open(os.path.join(ROOT, "data", "akademia_seed.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: len(v) for k, v in out.items() if isinstance(v, list)})
