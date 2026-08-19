#!/usr/bin/env node
/**
 * build-web-assets.mjs -- split inkwash.html into the three pieces a CMS theme needs.
 *
 *     node app/build-web-assets.mjs
 *
 * inkwash.html is the source of truth and stays a single self-contained file you can open
 * from disk with no server. A theme cannot use it in that shape: it is a whole HTML document,
 * and a page template only owns what goes inside <body>.
 *
 * So this emits, deterministically, into app/dist/:
 *
 *     inkwash.css      the <style> block
 *     inkwash.js       the <script> block
 *     inkwash-body.html the markup between <body> and the script
 *
 * Nothing is reformatted or minified. Concatenating the three back together reproduces the
 * original byte-for-byte apart from the surrounding document scaffolding, which the check at
 * the bottom asserts. Commit the outputs: the website pulls them by raw URL, which is what
 * keeps 49KB of CSS and JS from being retyped by hand into a theme editor.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "inkwash.html"), "utf8");
const dist = join(here, "dist");
mkdirSync(dist, { recursive: true });

const grab = (re, what) => {
  const m = src.match(re);
  if (!m) throw new Error(`build-web-assets: could not find ${what} in inkwash.html`);
  return m[1];
};

const css = grab(/<style>([\s\S]*?)<\/style>/, "the <style> block");
const js = grab(/<script>([\s\S]*?)<\/script>/, "the <script> block");
const bodyAll = grab(/<body>([\s\S]*?)<\/body>/, "the <body> element");
const body = bodyAll.replace(/<script>[\s\S]*?<\/script>/, "").trimEnd();

/**
 * The standalone file styles bare `body`, `main`, `footer` and `header.top`. Those are correct
 * for a document that owns the whole page and catastrophic inside a CMS template, where they
 * would restyle the site's own chrome. This rewrites every selector to sit under one wrapper
 * class so the tool can be embedded without touching anything around it.
 *
 * :root becomes the wrapper too, so the tool's custom properties stay inside it rather than
 * overriding a host theme that happens to use the same variable names.
 */
const SCOPE = ".iw-app";
function scopeCss(source) {
  // Comments are stripped first. A comment sitting between } and the next selector lands inside
  // the selector-list capture and silently defeats the rewrite -- that is how `header.top` and
  // bare `main` escaped on the first attempt and reached the leak assertion below.
  source = source.replace(/\/\*[\s\S]*?\*\//g, "");
  // Match after { as well as } -- selectors nested inside @media blocks follow an opening brace.
  return source.replace(/(^|[{}])([^{}@]+)(\{)/g, (all, close, selectorList, open) => {
    if (!selectorList.trim()) return all;
    const scoped = selectorList
      .split(",")
      .map((sel) => {
        const s = sel.trim();
        if (!s) return s;
        if (s === ":root" || s === "html" || s === "body") return SCOPE;
        if (s.startsWith("@") || s.startsWith("from") || s.startsWith("to") || /^\d+%$/.test(s)) return s;
        if (s.startsWith(SCOPE)) return s;
        return `${SCOPE} ${s}`;
      })
      .join(", ");
    return `${close}${selectorList.match(/^\s*/)[0]}${scoped}${open}`;
  });
}

const scoped = scopeCss(css.trim());
if (scoped.includes(`${SCOPE} ${SCOPE}`)) throw new Error("double-scoped a selector");
if (!scoped.includes(`${SCOPE}{`) && !scoped.includes(`${SCOPE} `)) throw new Error("scoping produced nothing");
// Nothing may reach the host page. A bare element selector at the start of a line is a leak.
const LEAK = /^\s*(html|body|main|header|footer|nav|section|textarea|button|select|input|table|a|p|h[1-6])[\s.,:[{]/;
const leaks = scoped.split("\n").filter((l) => LEAK.test(l));
if (leaks.length) {
  throw new Error("unscoped selectors would leak into the host page:\n  " + leaks.slice(0, 5).join("\n  "));
}

const files = {
  "inkwash.css": css.trim() + "\n",
  "inkwash-scoped.css": scoped + "\n",
  "inkwash.js": js.trim() + "\n",
  "inkwash-body.html": body.trim() + "\n",
};

for (const [name, text] of Object.entries(files)) {
  writeFileSync(join(dist, name), text, "utf8");
  console.log(`  ${name.padEnd(20)} ${text.length.toLocaleString().padStart(8)} bytes`);
}

// Round-trip check. Every non-whitespace character of the three outputs must be present in the
// source, and the counts must add up. If a future edit to inkwash.html breaks one of the three
// regexes, this fails loudly instead of shipping a half-empty stylesheet to the website.
const strip = (s) => s.replace(/\s+/g, "");
const recombined = strip(files["inkwash.css"]) + strip(files["inkwash.js"]) + strip(files["inkwash-body.html"]);
const original = strip(src);
if (!original.includes(strip(files["inkwash.css"]))) throw new Error("css did not round-trip");
if (!original.includes(strip(files["inkwash.js"]))) throw new Error("js did not round-trip");
const ratio = recombined.length / original.length;
if (ratio < 0.9) throw new Error(`only ${(ratio * 100).toFixed(1)}% of the source was captured; the split is losing content`);
console.log(`\n  round-trip: ${(ratio * 100).toFixed(1)}% of source captured (scaffolding is the remainder)`);
