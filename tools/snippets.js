// Renders the reused share/social snippets (vendor/share.js, vendor/social.js copied from jQrgen/presentations src/) as JSON for build.py
const share = require("../vendor/share.js");
const SOURCE = "https://github.com/jQrgen/kryptonytt"; // origin of this repo (git remote)
const [url, title, lang = "nb"] = process.argv.slice(2);
process.stdout.write(JSON.stringify({ top: share.top({ url, title, lang, source: { href: SOURCE } }), bar: share.bar({ url, title, lang }), css: share.CSS, script: share.SCRIPT }));
