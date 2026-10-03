"""Nyheitsbrev på Kryptonytt Norge: skjema i botnen av kvar side og sida /nyhetsbrev/ (nn: /, nb: /bm/, en: /en/).
AV som standard: berre når newsletter/config.json har enabled = true (eller KRYPTONYTT_NEWSLETTER=1 i testbygg) OG det
finst ei endepunktadresse (NEWSLETTER_ENDPOINT eller config.endpoint). Skjemaet sender til tipworker i Nordic Crypto-repoet
(POST /api/subscribe, site=kryptonytt; dobbel stadfesting). Synleg tekst: «kunstig intelligens», aldri AI eller KI."""
import json, os
import build as B
from build import L, E, P, S, load, page, out_dir
CFG = load(P("newsletter", "config.json"), {}) or {}

def endpoint():
    if not (CFG.get("enabled") is True or os.environ.get("KRYPTONYTT_NEWSLETTER") == "1"): return None
    e = os.environ.get("NEWSLETTER_ENDPOINT") or CFG.get("endpoint")
    return (e or "").strip().rstrip("/") or None

def T(k):
    return {
     "title": L("Nyheitsbrev", "Nyhetsbrev", "Newsletter"),
     "desc": L("Få ein kort e-post kvar veke med dei norske kryptonyheitene redaktøren vår har godkjent.", "Få en kort e-post hver uke med de norske kryptonyhetene redaktøren vår har godkjent.", "Get a short weekly email with the Norwegian crypto news our editor has approved."),
     "lead": L("Eit kort samandrag kvar veke av norske nyheiter om bitcoin, blokkjede og krypto som redaktøren vår har godkjent – overskrift, eit kort samandrag og lenkje til kjelda. Gratis og utan reklame.",
               "Et kort sammendrag hver uke av norske nyheter om bitcoin, blokkjede og krypto som redaktøren vår har godkjent – overskrift, et kort sammendrag og lenke til kilden. Gratis og uten reklame.",
               "A short weekly digest of Norwegian news about bitcoin, blockchain and crypto that our editor has approved – headline, a short summary and a link to the source. Free, no ads."),
     "email": L("E-postadresse", "E-postadresse", "Email address"), "btn": L("Abonner", "Abonner", "Subscribe"),
     "foot": L("Nyheitsbrev: eit kort samandrag kvar veke på e-post.", "Nyhetsbrev: et kort sammendrag hver uke på e-post.", "Newsletter: a short weekly digest by email."),
     "more": L("Meir om nyheitsbrevet", "Mer om nyhetsbrevet", "More about the newsletter"),
     "priv": L("<b>Personvern:</b> vi lagrar berre e-postadressa di, språket du valde og tidspunktet – <b>ikkje</b> IP-adressa di, og inga sporing. Du får ein e-post der du må stadfeste abonnementet; før det får du ingenting meir, og adresser som ikkje blir stadfesta, blir sletta etter 7 dagar. Kvart nyheitsbrev har ei lenkje for å melde seg av. Lista blir berre brukt til nyheitsbrevet frå Kryptonytt Norge og kan bli flytta til tenesta vi sender det med (til dømes Substack); ho blir aldri seld eller delt til noko anna. Påmeldinga går gjennom den same tenesta på Cloudflare som tipsboksen til søsterstaden Nordic Crypto.",
               "<b>Personvern:</b> vi lagrer bare e-postadressen din, språket du valgte og tidspunktet – <b>ikke</b> IP-adressen din, og ingen sporing. Du får en e-post der du må bekrefte abonnementet; før det får du ikke noe mer, og adresser som ikke bekreftes, slettes etter 7 dager. Hvert nyhetsbrev har en lenke for å melde seg av. Listen brukes bare til nyhetsbrevet fra Kryptonytt Norge og kan bli flyttet til tjenesten vi sender det med (for eksempel Substack); den blir aldri solgt eller delt til noe annet. Påmeldingen går gjennom den samme tjenesten på Cloudflare som tipsboksen til søsternettstedet Nordic Crypto.",
               "<b>Privacy:</b> we store only your email address, the language you chose and the time – <b>not</b> your IP address, and no tracking. You’ll get an email asking you to confirm; until you do, nothing more is sent, and unconfirmed addresses are deleted after 7 days. Every newsletter has an unsubscribe link. The list is used only for the Kryptonytt Norge newsletter and may be moved to the service we send it with (for example Substack); it is never sold or shared for anything else. Signups go through the same Cloudflare service as the tip box of our sister site Nordic Crypto."),
     "kaupr": L("<b>Openheit:</b> Kaupr (kaupr.io) er sponsor av Kryptonytt og ei av kjeldene våre.", "<b>Åpenhet:</b> Kaupr (kaupr.io) er sponsor av Kryptonytt og en av kildene våre.", "<b>Disclosure:</b> Kaupr (kaupr.io) sponsors Kryptonytt and is one of our sources."),
     "sending": L("Sender …", "Sender …", "Sending…"),
     "sent": L("Nesten ferdig: sjå i innboksen din og opne stadfestingslenkja innan 7 dagar.", "Nesten ferdig: sjekk innboksen din og åpne bekreftelseslenken innen 7 dager.", "Almost done: check your inbox and open the confirmation link within 7 days."),
     "confirmed": L("Takk, abonnementet ditt er stadfesta.", "Takk, abonnementet ditt er bekreftet.", "Thanks, your subscription is confirmed."),
     "unsub": L("Du er no meld av nyheitsbrevet.", "Du er nå meldt av nyhetsbrevet.", "You have been unsubscribed from the newsletter."),
     "e_email": L("Skriv inn ei gyldig e-postadresse.", "Skriv inn en gyldig e-postadresse.", "Please enter a valid email address."),
     "e_rate": L("For mange forsøk på kort tid. Prøv igjen seinare.", "For mange forsøk på kort tid. Prøv igjen senere.", "Too many attempts in a short time. Please try again later."),
     "e_link": L("Lenkja er ugyldig eller har gått ut. Meld deg på på nytt.", "Lenken er ugyldig eller har utløpt. Meld deg på på nytt.", "The link is invalid or has expired. Please sign up again."),
     "e_fail": L("Noko gjekk gale. Prøv igjen seinare.", "Noe gikk galt. Prøv igjen senere.", "Something went wrong. Please try again later."),
    }[k]

CSS = (".nlform{margin:12px 0}.nlform input[type=email]{padding:6px;width:100%;max-width:320px}.nlform button{padding:7px 14px;font-size:15px}"
       ".nlform .hp{position:absolute;left:-9999px}.nlmsg{display:block;margin-top:6px}.nlmsg.ok{color:#14532d}.nlmsg.warn{color:#9a3412}"
       ".nlfoot{margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #ddd}.nlfoot .nlform{display:inline}.nlc label{position:absolute;left:-9999px}")
_N = [0]
def form(compact=False):
    ep = endpoint()
    if not ep: return ""
    _N[0] += 1; i = _N[0]
    return (f'<form class="nlform{" nlc" if compact else ""}" method="post" action="{E(ep)}/api/subscribe" data-ep="{E(ep)}">'
            f'<input type="hidden" name="site" value="kryptonytt"><input type="hidden" name="lang" value="{S.lang}">'
            f'<label for="nl-email-{i}">{E(T("email"))}</label> <input id="nl-email-{i}" name="email" type="email" required maxlength="254" autocomplete="email" inputmode="email">'
            f'<span class="hp" aria-hidden="true"><label for="nl-w-{i}">website</label><input id="nl-w-{i}" name="website" tabindex="-1" autocomplete="off"></span>'
            f' <button type="submit">{E(T("btn"))}</button><span class="nlmsg" role="status" aria-live="polite"></span></form>')

def footer(home, slug):
    if not endpoint() or slug == "nyhetsbrev": return ""
    return f'<div class="nlfoot"><b>{E(T("foot"))}</b> {form(True)} <a href="{home}nyhetsbrev/">{E(T("more"))}</a></div>'

def script():
    if not endpoint(): return ""
    m = {k: T(k) for k in ("sending", "sent", "confirmed", "unsub", "e_email", "e_rate", "e_link", "e_fail")}
    return """<style>%s</style><script>(function(){var M=%s,F=[].slice.call(document.querySelectorAll('form.nlform'));if(!F.length)return;
function say(f,k){var s=f.querySelector('.nlmsg');s.textContent=M[k]||M.e_fail;s.className='nlmsg '+(k.indexOf('e_')===0?'warn':'ok')}
var E={email:'e_email',rate:'e_rate',invalid_link:'e_link'},q=new URLSearchParams(location.search),f0=document.querySelector('main form.nlform')||F[0];
if(q.get('sent'))say(f0,'sent');else if(q.get('confirmed'))say(f0,'confirmed');else if(q.get('unsubscribed'))say(f0,'unsub');else if(q.get('error'))say(f0,E[q.get('error')]||'e_fail');
F.forEach(function(f){f.addEventListener('submit',function(ev){ev.preventDefault();var b=f.querySelector('button'),d={};new FormData(f).forEach(function(v,k){d[k]=v});
b.disabled=true;say(f,'sending');fetch(f.getAttribute('data-ep')+'/api/subscribe',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(d)})
.then(function(r){return r.json().then(function(j){b.disabled=false;if(r.ok){say(f,'sent');f.reset()}else say(f,E[j.error]||'e_fail')})}).catch(function(){b.disabled=false;say(f,'e_fail')})})})})();</script>""" % (CSS, json.dumps(m, ensure_ascii=False))

def build_newsletter():
    if not endpoint(): return
    sub = CFG.get("substack_url")
    body = (f'<h1>{E(T("title"))}</h1>\n<p class="lead">{E(T("lead"))}</p>\n{form()}\n<div class="prose"><p class="notice">{T("priv")}</p>\n'
            + (f'<p><a href="{E(sub)}" rel="noopener">Substack</a></p>\n' if sub else "") + f'<p class="meta">{T("kaupr")}</p></div>')
    page("nyhetsbrev", T("title") + " – Kryptonytt Norge", "nyhetsbrev", body, T("desc"))
    d = out_dir("newsletter"); os.makedirs(d, exist_ok=True)   # /newsletter/ -> /nyhetsbrev/ (engelsk adresse)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
        '<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=../nyhetsbrev/">'
        '<link rel="canonical" href="../nyhetsbrev/"><title>→</title></head><body><a href="../nyhetsbrev/">→</a></body></html>')
