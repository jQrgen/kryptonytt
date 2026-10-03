"""«Slik blir reglane til»: animert flytskisse (statisk SVG + CSS, inga eiga JS utover sideramma) over korleis kryptoreglar
for Noreg blir laga og handheva. Kvar påstand har kjelde (Lovdata, EUR-Lex, Stortinget, Skatteetaten, Økokrim).
Påstandane er sjekka mot kjeldene 03.10.2026 (sjå research/reglar-kjeldesjekk.md). Side av til jQrgen godkjenner (reglar.enabled)."""
import build as B
from build import L, E, page, paths
LOV_MICA = "https://lovdata.no/dokument/NL/lov/2025-05-27-20"
LOV_HVIT = "https://lovdata.no/dokument/NL/lov/2018-06-01-23"
LOV_SENTRAL = "https://lovdata.no/dokument/NL/lov/2019-06-21-31"
EURLEX_MICA = "https://eur-lex.europa.eu/eli/reg/2023/1114/oj"
EURLEX_PROP = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52020PC0593"
EOS_AVT = "https://lovdata.no/dokument/TRAKTAT/traktat/1992-05-02-1"
UTGREIING = "https://lovdata.no/dokument/INS/forskrift/2016-02-19-184"
INNST = "https://www.stortinget.no/no/Saker-og-publikasjoner/Publikasjoner/Innstillinger/Stortinget/2024-2025/inns-202425-254l/"
SKATT = "https://www.skatteetaten.no/person/skatt/hjelp-til-riktig-skatt/aksjer-og-verdipapirer/om/virtuell-valuta/skatteregler---virtuell-valuta/"
OKO_AR = "https://okokrim.custompublish.com/aarsrapporter.616105.no.html"
FT_REG = "https://www.finanstilsynet.no/en/finanstilsynets-registry/"

# (id, x, y, w, klasse, tittel (nn, nb, en), undertittel (nn, nb, en), org-id eller None, (kjelde-url, kjeldenamn))
N = [
 ("kom", 20, 20, 210, "eu", ("Europakommisjonen", "Europakommisjonen", "European Commission"), ("føreslår regelverket", "foreslår regelverket", "proposes the rules"), None, (EURLEX_PROP, "EUR-Lex: COM(2020) 593")),
 ("epr", 270, 20, 250, "eu", ("Europaparlamentet og Rådet", "Europaparlamentet og Rådet", "European Parliament and Council"), ("vedtek MiCA (EU) 2023/1114", "vedtar MiCA (EU) 2023/1114", "adopt MiCA (EU) 2023/1114"), None, (EURLEX_MICA, "EUR-Lex: (EU) 2023/1114")),
 ("esma", 560, 20, 190, "eu", ("ESMA og EBA", "ESMA og EBA", "ESMA and EBA"), ("tekniske standardar", "tekniske standarder", "technical standards"), "esma", (EURLEX_MICA, "EUR-Lex: MiCA")),
 ("eos", 270, 130, 250, "eu", ("EØS-komiteen", "EØS-komiteen", "EEA Joint Committee"), ("tek MiCA inn i EØS-avtalen", "tar MiCA inn i EØS-avtalen", "incorporates MiCA into the EEA Agreement"), None, (EOS_AVT, "EØS-avtalen art. 102")),
 ("hoy", 20, 240, 210, "cons", ("Høyring", "Høring", "Public consultation"), ("bransjen og allmenta", "bransjen og allmennheten", "industry and the public"), None, (UTGREIING, "Utgreiingsinstruksen 3-3")),
 ("fin", 270, 240, 250, "pub", ("Finansdepartementet", "Finansdepartementet", "Ministry of Finance"), ("lovforslag: Prop. 55 LS (2024–2025)", "lovforslag: Prop. 55 LS (2024–2025)", "bill: Prop. 55 LS (2024–2025)"), "finansdepartementet", (LOV_MICA, "Lovdata")),
 ("sto", 560, 240, 190, "pub", ("Stortinget", "Stortinget", "Storting (parliament)"), ("vedtek lova, mai 2025", "vedtar loven, mai 2025", "passes the act, May 2025"), "stortinget-finanskomiteen", (INNST, "Innst. 254 L")),
 ("lov1", 20, 350, 240, "law", ("Kryptoeiendelsloven", "Kryptoeiendelsloven", "Crypto-Assets Act"), ("MiCA som norsk lov frå 1.7.2025", "MiCA som norsk lov fra 1.7.2025", "MiCA as Norwegian law from 1 Jul 2025"), "kryptoeiendelsloven", (LOV_MICA, "Lovdata")),
 ("lov2", 290, 350, 220, "law", ("Hvitvaskingsloven", "Hvitvaskingsloven", "Anti-Money Laundering Act"), ("rapportering, TFR II (§ 52)", "rapportering, TFR II (§ 52)", "reporting, TFR II (§ 52)"), None, (LOV_HVIT, "Lovdata")),
 ("lov3", 540, 350, 210, "law", ("Skattereglane", "Skattereglene", "Tax rules"), ("kryptoeigedelar er formuesobjekt", "kryptoeiendeler er formuesobjekter", "crypto-assets are taxable assets"), None, (SKATT, "Skatteetaten")),
 ("ft", 20, 470, 180, "pub", ("Finanstilsynet", "Finanstilsynet", "Finanstilsynet (FSA)"), ("tilsyn og løyve", "tilsyn og tillatelser", "supervision and licences"), "finanstilsynet", (LOV_MICA, "kryptoeiendelsloven § 2")),
 ("oko", 212, 470, 180, "pub", ("Økokrim og politiet", "Økokrim og politiet", "Økokrim and the police"), ("handheving", "håndheving", "enforcement"), "okokrim", (LOV_HVIT, "hvitvaskingsloven § 26")),
 ("skatt", 404, 470, 160, "pub", ("Skatteetaten", "Skatteetaten", "Tax Administration"), ("skatt", "skatt", "tax"), "skatteetaten", (SKATT, "Skatteetaten")),
 ("nb", 576, 470, 180, "pub", ("Noregs Bank", "Norges Bank", "Norges Bank"), ("betalingssystemet", "betalingssystemet", "payment system"), "norges-bank", (LOV_SENTRAL, "sentralbankloven § 1-2")),
]
EDGES = [("kom", "epr", "anim"), ("epr", "esma", "anim"), ("epr", "eos", "anim"), ("eos", "fin", "anim"), ("hoy", "fin", "consult"), ("fin", "sto", "anim"),
         ("sto", "lov1", "anim"), ("sto", "lov2", "anim"), ("sto", "lov3", "anim"), ("lov1", "ft", "anim"), ("lov2", "oko", "anim"), ("lov1", "oko", "anim"), ("lov3", "skatt", "anim")]  # Noregs Bank: inga pil; banken handhevar ikkje kryptoeiendelsloven
H = 62

def svg(home):
    by = {n[0]: n for n in N}
    def c(nid, side):
        _, x, y, w, *_ = by[nid]
        return {"b": (x + w / 2, y + H), "t": (x + w / 2, y), "r": (x + w, y + H / 2), "l": (x, y + H / 2)}[side]
    paths_ = []
    for a, b, cls in EDGES:
        ya, yb = by[a][2], by[b][2]
        if ya == yb: (x1, y1), (x2, y2) = (c(a, "r"), c(b, "l")) if by[a][1] < by[b][1] else (c(a, "l"), c(b, "r")); d = f"M{x1},{y1} L{x2 - 4},{y2}"
        else: (x1, y1), (x2, y2) = c(a, "b"), c(b, "t"); my = (y1 + y2) / 2; d = f"M{x1},{y1} C{x1},{my} {x2},{my} {x2},{y2 - 4}"
        paths_.append(f'<path class="edge {cls}" d="{d}"/>')
    nodes = []
    for i, (nid, x, y, w, cls, t, sub, org, (src, srcname)) in enumerate(N):
        title, st = L(*t), L(*sub)
        inner = (f'<rect x="{x}" y="{y}" width="{w}" height="{H}" rx="6"/><text x="{x + 10}" y="{y + 20}">{E(title)}</text><text class="s" x="{x + 10}" y="{y + 37}">{E(st)}</text>')
        main = f'<a href="{home}organisasjonskart/#{org}" aria-label="{E(title)} – {L("i organisasjonskartet", "i organisasjonskartet", "in the org chart")}">{inner}</a>' if org else inner
        srcl = f'<a href="{E(src)}" rel="noopener" target="_blank"><text class="s" x="{x + 10}" y="{y + 54}" text-decoration="underline">{L("Kjelde", "Kilde", "Source")}: {E(srcname)} ↗</text></a>'
        nodes.append(f'<g class="node {cls}" style="animation-delay:{i * 0.12:.2f}s">{main}{srcl}</g>')
    return (f'<svg viewBox="0 0 770 550" role="img" aria-labelledby="flowtitle flowdesc" xmlns="http://www.w3.org/2000/svg">'
            f'<title id="flowtitle">{L("Flytskisse: slik blir kryptoreglar for Noreg til og handheva", "Flytskisse: slik blir kryptoregler for Norge til og håndhevet", "Flowchart: how crypto rules for Norway are made and enforced")}</title>'
            f'<desc id="flowdesc">{L("Same innhald som lista «Steg for steg» under.", "Samme innhold som listen «Steg for steg» under.", "Same content as the step-by-step list below.")}</desc>'
            '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#4B5563"/></marker></defs>'
            + "".join(paths_) + "".join(nodes) + "</svg>")

def src(u, t): return f'<a href="{E(u)}" rel="noopener" target="_blank">{E(t)}</a>'
def org(home, oid, t): return f'<a href="{home}organisasjonskart/#{oid}">{E(t)}</a>'

def build():
    root, home = paths("reglar")
    oc = L("i organisasjonskartet", "i organisasjonskartet", "in the org chart")
    K = L("Kjelde", "Kilde", "Source"); KK = L("Kjelder", "Kilder", "Sources")
    steps = [
     (L("Europakommisjonen føreslår", "Europakommisjonen foreslår", "The European Commission proposes"),
      L("Kommisjonen legg fram forslag til nytt EU-regelverk. Forslaget til MiCA har nummeret COM(2020) 593.", "Kommisjonen legger fram forslag til nytt EU-regelverk. Forslaget til MiCA har nummeret COM(2020) 593.", "The Commission puts forward proposals for new EU legislation. The MiCA proposal is COM(2020) 593."),
      f"{K}: {src(EURLEX_PROP, 'EUR-Lex, COM(2020) 593')}"),
     (L("Europaparlamentet og Rådet vedtek", "Europaparlamentet og Rådet vedtar", "The European Parliament and the Council adopt"),
      L("MiCA er forordning (EU) 2023/1114 frå Europaparlamentet og Rådet, vedteken 31. mai 2023.", "MiCA er forordning (EU) 2023/1114 fra Europaparlamentet og Rådet, vedtatt 31. mai 2023.", "MiCA is Regulation (EU) 2023/1114 of the European Parliament and of the Council, adopted on 31 May 2023."),
      f"{K}: {src(EURLEX_MICA, 'EUR-Lex, forordning (EU) 2023/1114')}"),
     (L("ESMA og EBA utfyller", "ESMA og EBA utfyller", "ESMA and EBA fill in the details"),
      L("MiCA gir dei europeiske tilsynsorgana ESMA og EBA i oppdrag å utarbeide utkast til tekniske standardar som utfyller forordninga.", "MiCA gir de europeiske tilsynsorganene ESMA og EBA i oppdrag å utarbeide utkast til tekniske standarder som utfyller forordningen.", "MiCA mandates the European supervisory authorities ESMA and EBA to develop draft technical standards that fill in the regulation."),
      f"{K}: {src(EURLEX_MICA, 'EUR-Lex, MiCA')} · {org(home, 'esma', 'ESMA ' + oc)} · {org(home, 'eba', 'EBA ' + oc)}"),
     (L("EØS-komiteen tek regelverket inn i EØS-avtalen", "EØS-komiteen tar regelverket inn i EØS-avtalen", "The EEA Joint Committee incorporates the rules into the EEA Agreement"),
      L("EØS-komiteen avgjer endringar i vedlegga til EØS-avtalen når EU har vedteke nytt regelverk (artikkel 102). MiCA står i EØS-avtalen vedlegg IX nr. 31r.", "EØS-komiteen beslutter endringer i vedleggene til EØS-avtalen når EU har vedtatt nytt regelverk (artikkel 102). MiCA står i EØS-avtalen vedlegg IX nr. 31r.", "The EEA Joint Committee decides on amendments to the annexes of the EEA Agreement once the EU has adopted new legislation (Article 102). MiCA is listed in Annex IX, point 31r, of the EEA Agreement."),
      f"{KK}: {src(EOS_AVT, 'EØS-avtalen artikkel 102 (Lovdata)')} · {src(LOV_MICA, 'kryptoeiendelsloven § 1 (Lovdata)')}"),
     (L("Høyring: bransjen og allmenta seier meininga si", "Høring: bransjen og allmennheten sier sin mening", "Consultation: the industry and the public have their say"),
      L("Forslag til lover og forskrifter skal som hovudregel sendast på offentleg høyring før dei blir vedtekne, slik at bransjen, organisasjonar og alle andre kan kome med innspel.", "Forslag til lover og forskrifter skal som hovedregel sendes på offentlig høring før de vedtas, slik at bransjen, organisasjoner og alle andre kan komme med innspill.", "As a rule, draft acts and regulations must be sent out for public consultation before they are adopted, so the industry, organisations and anyone else can submit comments."),
      f"{K}: {src(UTGREIING, 'utgreiingsinstruksen kapittel 3 (Lovdata)')}"),
     (L("Finansdepartementet lagar lovforslaget", "Finansdepartementet lager lovforslaget", "The Ministry of Finance drafts the bill"),
      L("Kryptoeiendelsloven vart fremja av Finansdepartementet i Prop. 55 LS (2024–2025).", "Kryptoeiendelsloven ble fremmet av Finansdepartementet i Prop. 55 LS (2024–2025).", "The Crypto-Assets Act (kryptoeiendelsloven) was put forward by the Ministry of Finance in Prop. 55 LS (2024–2025)."),
      f"{K}: {src(LOV_MICA, 'Lovdata, LOV-2025-05-27-20')} · {org(home, 'finansdepartementet', 'Finansdepartementet ' + oc)}"),
     (L("Stortinget vedtek lova", "Stortinget vedtar loven", "The Storting passes the act"),
      L("Finanskomiteen gav innstilling i Innst. 254 L (2024–2025), og Stortinget behandla lova 15. og 20. mai 2025.", "Finanskomiteen ga innstilling i Innst. 254 L (2024–2025), og Stortinget behandlet loven 15. og 20. mai 2025.", "The Standing Committee on Finance issued its recommendation in Innst. 254 L (2024–2025), and the Storting considered the act on 15 and 20 May 2025."),
      f"{KK}: {src(INNST, 'Stortinget, Innst. 254 L')} · {src(LOV_MICA, 'Lovdata')} · {org(home, 'stortinget-finanskomiteen', L('Finanskomiteen', 'Finanskomiteen', 'Finance committee') + ' ' + oc)}"),
     (L("Lovene", "Lovene", "The acts"),
      L("Etter kryptoeiendelsloven § 1 gjeld MiCA som norsk lov, i kraft frå 1. juli 2025. Hvitvaskingsloven pålegg rapporteringspliktige å sende opplysningar til Økokrim ved mistanke om kvitvasking eller terrorfinansiering (§ 26), og § 52 gjer TFR II (forordning (EU) 2023/1113) om opplysningar som skal følgje overføringar av pengar og visse kryptoeigedelar, til norsk lov. Skattemessig er kryptoeigedelar formuesobjekt, og inntekter frå dei er skattepliktige.",
        "Etter kryptoeiendelsloven § 1 gjelder MiCA som norsk lov, i kraft fra 1. juli 2025. Hvitvaskingsloven pålegger rapporteringspliktige å sende opplysninger til Økokrim ved mistanke om hvitvasking eller terrorfinansiering (§ 26), og § 52 gjør TFR II (forordning (EU) 2023/1113) om opplysninger som skal følge overføringer av penger og visse kryptoeiendeler, til norsk lov. Skattemessig er kryptoeiendeler formuesobjekter, og inntekter fra dem er skattepliktige.",
        "Under section 1 of the Crypto-Assets Act, MiCA applies as Norwegian law, in force from 1 July 2025. The Anti-Money Laundering Act requires reporting entities to send information to Økokrim when they suspect money laundering or terrorist financing (section 26), and section 52 makes TFR II (Regulation (EU) 2023/1113) on information accompanying transfers of funds and certain crypto-assets Norwegian law. For tax purposes, crypto-assets are treated as assets, and income from them is taxable."),
      f"{KK}: {src(LOV_MICA, 'kryptoeiendelsloven (Lovdata)')} · {src(LOV_HVIT, 'hvitvaskingsloven (Lovdata)')} · {src(SKATT, 'Skatteetaten: skatteregler for virtuelle eiendeler')} · {org(home, 'kryptoeiendelsloven', 'Kryptoeiendelsloven ' + oc)}"),
     (L("Finanstilsynet: tilsyn og løyve", "Finanstilsynet: tilsyn og tillatelser", "Finanstilsynet: supervision and licences"),
      L("Finanstilsynet er tilsynsmyndigheit og fører tilsyn med føretak som har løyve etter kryptoeiendelsforordninga (kryptoeiendelsloven § 2). Lova har mellom anna reglar om pålegg (§ 5), tilbakekall av løyve (§ 12) og straff (§ 18). Føretak med løyve er oppførte i registeret til Finanstilsynet.",
        "Finanstilsynet er tilsynsmyndighet og fører tilsyn med foretak som har tillatelse etter kryptoeiendelsforordningen (kryptoeiendelsloven § 2). Loven har blant annet regler om pålegg (§ 5), tilbakekall av tillatelse (§ 12) og straff (§ 18). Foretak med tillatelse står i Finanstilsynets register.",
        "Finanstilsynet is the supervisory authority and supervises firms licensed under the crypto-assets regulation (section 2 of the Crypto-Assets Act). Among other things, the act has rules on orders (section 5), revocation of licences (section 12) and penalties (section 18). Licensed firms are listed in Finanstilsynet’s register."),
      f"{KK}: {src(LOV_MICA, 'kryptoeiendelsloven §§ 2, 5, 12, 18 (Lovdata)')} · {src(FT_REG, L('registeret til Finanstilsynet', 'Finanstilsynets register', 'Finanstilsynet’s register'))} · {org(home, 'finanstilsynet', 'Finanstilsynet ' + oc)}"),
     (L("Økokrim og politiet: handheving", "Økokrim og politiet: håndheving", "Økokrim and the police: enforcement"),
      L("Økokrim tek imot rapportar om mistenkjelege transaksjonar etter hvitvaskingsloven § 26. Ifølgje årsrapporten for 2025 har Økokrim ei eiga kryptovalutagruppe. Kryptoeiendelsloven § 15 har reglar om bistand frå politiet til tilsynet.",
        "Økokrim mottar rapporter om mistenkelige transaksjoner etter hvitvaskingsloven § 26. Ifølge årsrapporten for 2025 har Økokrim en egen kryptovalutagruppe. Kryptoeiendelsloven § 15 har regler om bistand fra politiet til tilsynet.",
        "Økokrim receives suspicious transaction reports under section 26 of the Anti-Money Laundering Act. According to its 2025 annual report, Økokrim has a dedicated cryptocurrency group. Section 15 of the Crypto-Assets Act has rules on police assistance to the supervisor."),
      f"{KK}: {src(LOV_HVIT, 'hvitvaskingsloven § 26 (Lovdata)')} · {src(OKO_AR, L('Økokrim, årsrapportar', 'Økokrim, årsrapporter', 'Økokrim, annual reports'))} · {src(LOV_MICA, 'kryptoeiendelsloven § 15 (Lovdata)')} · {org(home, 'okokrim', 'Økokrim ' + oc)}"),
     (L("Skatteetaten: skatt", "Skatteetaten: skatt", "Tax Administration: tax"),
      L("Gevinst, inntekt og formue i kryptoeigedelar skal oppgjevast i skattemeldinga. Inntekt blir skattlagd som kapitalinntekt med 22 prosent.", "Gevinst, inntekt og formue i kryptoeiendeler skal oppgis i skattemeldingen. Inntekt skattlegges som kapitalinntekt med 22 prosent.", "Gains, income and wealth in crypto-assets must be reported in the tax return. Income is taxed as capital income at 22 per cent."),
      f"{K}: {src(SKATT, 'Skatteetaten: skatteregler for virtuelle eiendeler')} · {org(home, 'skatteetaten', 'Skatteetaten ' + oc)}"),
     (L("Noregs Bank, der det er relevant", "Norges Bank, der det er relevant", "Norges Bank, where relevant"),
      L("Noregs Bank skal mellom anna fremje stabilitet i det finansielle systemet og eit effektivt og sikkert betalingssystem (sentralbanklova § 1-2). Banken fører ikkje tilsyn etter kryptoeiendelsloven.",
        "Norges Bank skal blant annet fremme stabilitet i det finansielle systemet og et effektivt og sikkert betalingssystem (sentralbankloven § 1-2). Banken fører ikke tilsyn etter kryptoeiendelsloven.",
        "Norges Bank’s purposes include promoting financial stability and an efficient and secure payment system (section 1-2 of the Central Bank Act). It is not the supervisor under the Crypto-Assets Act."),
      f"{KK}: {src(LOV_SENTRAL, 'sentralbankloven § 1-2 (Lovdata)')} · {src(LOV_MICA, 'kryptoeiendelsloven § 2 (Lovdata)')} · {org(home, 'norges-bank', 'Norges Bank ' + oc)}"),
    ]
    lis = "".join(f'<li><b>{E(t)}</b><br>{E(x)}<div class="src">{s}</div></li>' for t, x, s in steps)
    body = f"""<h1>{L("Slik blir reglane til", "Slik blir reglene til", "How the rules are made")}</h1>
<p class="lead">{L("Korleis kryptoreglar for Noreg blir laga i EU, tekne inn gjennom EØS, vedtekne i Noreg og handheva. Pilene viser vegen; kvar boks lenkjer til aktøren i organisasjonskartet og til kjelda.",
"Hvordan kryptoregler for Norge blir laget i EU, tatt inn gjennom EØS, vedtatt i Norge og håndhevet. Pilene viser veien; hver boks lenker til aktøren i organisasjonskartet og til kilden.",
"How crypto rules for Norway are made in the EU, brought in through the EEA, adopted in Norway and enforced. The arrows show the path; each box links to the organisation in the org chart and to its source.")}</p>
<p class="meta"><a href="{home}organisasjonskart/">{L("← Kven er kven", "← Hvem er hvem", "← Who’s who")}</a> · <a href="{home}organisasjonskart/#industrikart">{L("Industrikart", "Industrikart", "Industry map")}</a></p>
<figure class="flow">{svg(home)}<figcaption class="meta">{L("Stipla oransje pil: høyring. Animasjonen stoppar om du har slått på redusert rørsle.", "Stiplet oransje pil: høring. Animasjonen stopper hvis du har slått på redusert bevegelse.", "Dotted orange arrow: consultation. The animation stops if you have reduced motion turned on.")}</figcaption></figure>
<h2 id="steg">{L("Steg for steg", "Steg for steg", "Step by step")}</h2>
<ol class="steps">{lis}</ol>
<p class="notice">{L("Forenkla oversikt, ikkje juridisk rådgjeving. Påstandane er sjekka mot kjeldene 3. oktober 2026. Ser du ein feil? Sei frá på", "Forenklet oversikt, ikke juridisk rådgivning. Påstandene er sjekket mot kildene 3. oktober 2026. Ser du en feil? Si fra på", "A simplified overview, not legal advice. The claims were checked against the sources on 3 October 2026. Spotted an error? Tell us on")} <a href="https://github.com/jQrgen/kryptonytt/issues" rel="noopener">GitHub</a>.</p>"""
    if B.S.lang == "nn": body = body.replace("Sei frá på", "Sei frå på")
    page("reglar", L("Slik blir reglane til – kryptoreglar for Noreg", "Slik blir reglene til – kryptoregler for Norge", "How the rules are made – crypto rules for Norway"), "reglar", body,
         L("Animert flytskisse over korleis kryptoreglar for Noreg blir laga i EU, tekne inn via EØS, vedtekne av Stortinget og handheva av Finanstilsynet, Økokrim og Skatteetaten.",
           "Animert flytskisse over hvordan kryptoregler for Norge blir laget i EU, tatt inn via EØS, vedtatt av Stortinget og håndhevet av Finanstilsynet, Økokrim og Skatteetaten.",
           "Animated flowchart of how crypto rules for Norway are made in the EU, brought in via the EEA, passed by the Storting and enforced by Finanstilsynet, Økokrim and the Tax Administration."))
