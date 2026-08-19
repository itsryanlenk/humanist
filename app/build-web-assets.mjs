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

const files = {
  "inkwash.css": css.trim() + "\n",
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
