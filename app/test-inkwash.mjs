/* Headless test for the Inkwash engine.
   Extracts the engine half of inkwash.html (everything before the UI section),
   evaluates it, and asserts against hand-built vectors.
   Run:  node app/test-inkwash.mjs                                            */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "inkwash.html"), "utf8");

const script = html.split(/<script>/)[1].split(/<\/script>/)[0];
const UI_MARK = script.indexOf("   UI\n");
if (UI_MARK < 0) throw new Error("could not find the UI section marker");
const engineSrc = script.slice(0, script.lastIndexOf("/* =====", UI_MARK));

const engine = new Function(engineSrc + "\n;return {wash, hex, CATEGORIES, ZERO_WIDTH, TYPO, HOMOGLYPH};")();
const { wash, CATEGORIES } = engine;

const S = (cp) => String.fromCodePoint(cp);
const ALL_ON = Object.fromEntries(CATEGORIES.map((c) => [c.id, true]));
const OPTS = { ...ALL_ON, dash: " - " };

let pass = 0,
  fail = 0;
const checks = [];

function t(name, fn) {
  try {
    fn();
    pass++;
    checks.push(["PASS", name, ""]);
  } catch (e) {
    fail++;
    checks.push(["FAIL", name, e.message]);
  }
}
function eq(actual, expected, label) {
  if (actual !== expected) {
    throw new Error(`${label || ""} expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}
function has(hits, cat, action) {
  if (!hits.some((h) => h.cat === cat && h.action === action)) {
    throw new Error(`no ${cat}/${action} hit in [${hits.map((h) => h.cat + "/" + h.action).join(", ")}]`);
  }
}
function none(hits, cat, action) {
  if (hits.some((h) => h.cat === cat && h.action === action)) {
    throw new Error(`unexpected ${cat}/${action} hit`);
  }
}

/* ---------------------------------------------------------------- removal */
t("zero-width space is removed", () => {
  const r = wash("ab" + S(0x200b) + "cd", OPTS);
  eq(r.result, "abcd");
  has(r.hits, "zerowidth", "removed");
});

t("soft hyphen is removed", () => {
  eq(wash("co" + S(0x00ad) + "operate", OPTS).result, "cooperate");
});

t("BOM is removed", () => {
  eq(wash(S(0xfeff) + "Title", OPTS).result, "Title");
});

t("word joiner and invisible math operators are removed", () => {
  const r = wash("a" + S(0x2060) + "b" + S(0x2062) + "c", OPTS);
  eq(r.result, "abc");
});

t("bidi override is removed", () => {
  const r = wash("safe" + S(0x202e) + "text", OPTS);
  eq(r.result, "safetext");
  has(r.hits, "bidi", "removed");
});

/* ------------------------------------------------------------- whitespace */
t("nbsp becomes a plain space", () => {
  const r = wash("9" + S(0x00a0) + "hours", OPTS);
  eq(r.result, "9 hours");
  has(r.hits, "spaces", "replaced");
});

t("thin space becomes a plain space", () => {
  eq(wash("14" + S(0x2009) + "kg", OPTS).result, "14 kg");
});

t("line separator becomes a newline", () => {
  eq(wash("a" + S(0x2028) + "b", OPTS).result, "a\nb");
});

/* ------------------------------------------------------------- typography */
t("curly quotes become straight", () => {
  eq(wash(S(0x201c) + "hold" + S(0x201d) + " and " + S(0x2018) + "wait" + S(0x2019), OPTS).result, '"hold" and \'wait\'');
});

t("ellipsis character becomes three dots", () => {
  eq(wash("wait" + S(0x2026), OPTS).result, "wait...");
});

t("en dash becomes a hyphen", () => {
  eq(wash("9" + S(0x2013) + "14", OPTS).result, "9-14");
});

t("em dash honors the selected replacement", () => {
  eq(wash("a" + S(0x2014) + "b", { ...OPTS, dash: " - " }).result, "a - b");
  eq(wash("a" + S(0x2014) + "b", { ...OPTS, dash: "--" }).result, "a--b");
  eq(wash("a" + S(0x2014) + "b", { ...OPTS, dash: "KEEP" }).result, "a" + S(0x2014) + "b");
});

t("arrows become typed equivalents", () => {
  eq(wash("a" + S(0x2192) + "b", OPTS).result, "a->b");
});

t("fullwidth forms fold to ASCII", () => {
  eq(wash("ＨＥＬＬＯ", OPTS).result, "HELLO");
});

/* -------------------------------------------------------------- homoglyph */
t("cyrillic es inside a latin word is corrected", () => {
  const r = wash("the " + S(0x0441) + "ontact sheet", OPTS);
  eq(r.result, "the contact sheet");
  has(r.hits, "homoglyph", "replaced");
});

t("a wholly cyrillic word is left alone", () => {
  const src = "the word " + S(0x0441) + S(0x043e) + S(0x0432);
  const r = wash(src, OPTS);
  eq(r.result, src, "genuine cyrillic must survive");
  none(r.hits, "homoglyph", "replaced");
});

t("a wholly greek word is left alone", () => {
  const src = "value " + S(0x03b1) + S(0x03b2) + S(0x03b3);
  eq(wash(src, OPTS).result, src);
});

/* ---------------------------------------------------------------- joiners */
t("emoji ZWJ sequence survives the wash", () => {
  const fam = "\u{1F469}" + S(0x200d) + "\u{1F4BB}";
  const r = wash("dev " + fam + " here", OPTS);
  eq(r.result, "dev " + fam + " here", "emoji must not be broken");
  has(r.hits, "joiners", "kept");
});

t("stray ZWJ between latin letters is removed", () => {
  const r = wash("ab" + S(0x200d) + "cd", OPTS);
  eq(r.result, "abcd");
  has(r.hits, "joiners", "removed");
});

t("VS16 after a pictograph is kept", () => {
  const heart = "❤" + S(0xfe0f);
  const r = wash("love " + heart, OPTS);
  eq(r.result, "love " + heart);
  has(r.hits, "varsel", "kept");
});

t("stray variation selector after a letter is removed", () => {
  const r = wash("My" + S(0xfe01) + " notes", OPTS);
  eq(r.result, "My notes");
  has(r.hits, "varsel", "removed");
});

/* ------------------------------------------- deprecated & script formats */
t("deprecated format controls are removed", () => {
  const r = wash("word" + S(0x206e) + "word", OPTS);
  eq(r.result, "wordword");
  has(r.hits, "deprecated", "removed");
});

t("interlinear annotation marks are removed", () => {
  // U+FFF9..FFFB can make displayed text differ from stored text.
  const src = "safe" + S(0xfff9) + "shown" + S(0xfffa) + "hidden" + S(0xfffb) + "text";
  const r = wash(src, OPTS);
  eq(r.result, "safeshownhiddentext");
  has(r.hits, "deprecated", "removed");
});

t("musical and shorthand format controls are removed", () => {
  eq(wash("a" + S(0x1d173) + "b" + S(0x1bca0) + "c", OPTS).result, "abc");
});

t("arabic end-of-ayah is KEPT inside arabic text", () => {
  const src = "القرآن" + S(0x06dd) + "الكريم";
  const r = wash(src, OPTS);
  eq(r.result, src, "genuine Arabic must survive untouched");
  has(r.hits, "joiners", "kept");
});

t("arabic end-of-ayah is removed when adrift in english", () => {
  const r = wash("the report" + S(0x06dd) + " said so", OPTS);
  eq(r.result, "the report said so");
  has(r.hits, "joiners", "removed");
});

t("syriac abbreviation mark is kept inside syriac text", () => {
  const src = "ܐܒܓ" + S(0x070f) + "ܕܖ";
  eq(wash(src, OPTS).result, src);
});

t("egyptian hieroglyph controls are kept inside hieroglyphic text", () => {
  const src = "\u{13000}\u{13001}" + S(0x13430) + "\u{13002}";
  eq(wash(src, OPTS).result, src);
});

t("egyptian hieroglyph control is removed when adrift in english", () => {
  const r = wash("plain english" + S(0x13430) + " here", OPTS);
  eq(r.result, "plain english here");
  has(r.hits, "joiners", "removed");
});

/* ------------------------------------------------------------- smuggling */
t("unicode tag payload is decoded and stripped", () => {
  const tag = (s) => Array.from(s).map((c) => S(0xe0000 + c.charCodeAt(0))).join("");
  const r = wash("Ordinary sentence." + tag("secret-id-42"), OPTS);
  eq(r.result, "Ordinary sentence.");
  eq(r.smuggled, "secret-id-42");
  has(r.hits, "tags", "removed");
});

/* ------------------------------------------------------------------ tidy */
t("CRLF folds to LF", () => {
  eq(wash("a\r\nb", OPTS).result, "a\nb");
});

t("trailing whitespace goes", () => {
  eq(wash("line one   \nline two\t\n", OPTS).result, "line one\nline two\n");
});

t("runs of blank lines collapse to one", () => {
  eq(wash("a\n\n\n\n\nb", OPTS).result, "a\n\nb");
});

t("double spaces collapse but newlines survive", () => {
  eq(wash("a  b\n\nc", OPTS).result, "a b\n\nc");
});

/* ------------------------------------------------------------- switch off */
t("a disabled category reports but does not change the text", () => {
  const off = { ...OPTS, zerowidth: false };
  const src = "ab" + S(0x200b) + "cd";
  const r = wash(src, off);
  eq(r.result, src, "text must be untouched");
  has(r.hits, "zerowidth", "kept");
});

t("clean prose passes through byte-identical", () => {
  const src = "I reprinted the contact sheet on Tuesday.\n\nIt came out muddy twice.";
  const r = wash(src, OPTS);
  eq(r.result, src);
  eq(r.hits.filter((h) => h.action !== "kept").length, 0, "no changes expected");
});

/* --------------------------------------------------------------- robustness */
t("empty input does not throw", () => {
  const r = wash("", OPTS);
  eq(r.result, "");
  eq(r.hits.length, 0);
});

t("astral plane characters survive intact", () => {
  const src = "math \u{1D538} and emoji \u{1F600} together";
  eq(wash(src, OPTS).result, src);
});

t("a large document completes quickly", () => {
  const src = ("The kiln cooled too fast" + S(0x200b) + " and the glaze crazed. ").repeat(4000);
  const t0 = process.hrtime.bigint();
  const r = wash(src, OPTS);
  const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  if (ms > 4000) throw new Error(`took ${ms.toFixed(0)}ms on ${src.length} chars`);
  if (r.result.includes(S(0x200b))) throw new Error("zero-width survived a large input");
  checks.push(["note", "large doc timing", `${src.length.toLocaleString()} chars in ${ms.toFixed(0)}ms`]);
});

/* -------------------------------------------------------------------------- */
const width = Math.max(...checks.map((c) => c[1].length));
for (const [status, name, msg] of checks) {
  console.log(`${status.padEnd(5)} ${name.padEnd(width)}  ${msg}`);
}
console.log(`\n${pass} passed, ${fail} failed.`);
process.exit(fail ? 1 : 0);
