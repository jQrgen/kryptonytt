// Renders the reused share/social snippets (vendor/share.js, vendor/social.js copied from jQrgen/presentations src/) as JSON for build.py
const share = require("../vendor/share.js");
const [url, title] = process.argv.slice(2);
process.stdout.write(JSON.stringify({ top: share.top({ url, title, lang: "no" }), bar: share.bar({ url, title, lang: "no" }), css: share.CSS, script: share.SCRIPT }));
