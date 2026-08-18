/* Integration test for Inkwash's .docx and .html import.

   The ZIP reader in inkwash.html is hand-written against the spec, so this builds a
   real ZIP byte-for-byte (both deflate and stored entries, correct central-directory
   offsets) and checks the parser gets the prose and the metadata back out.

   Run:  node app/test-docx.mjs                                                */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { deflateRawSync } from "node:zlib";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "inkwash.html"), "utf8");

// Pull out just the document-import section and evaluate it.
const script = html.split(/<script>/)[1].split(/<\/script>/)[0];
const start = script.indexOf("   DOCUMENT IMPORT");
const uiMark = script.indexOf("   UI\n");
if (start < 0 || uiMark < 0) throw new Error("could not locate the DOCUMENT IMPORT section");
const src = script.slice(script.lastIndexOf("/* =====", start), script.lastIndexOf("/* =====", uiMark));

// Minimal DOM stub: the extractor uses a detached textarea to unescape entities.
globalThis.document = {
  createElement: () => ({
    set innerHTML(v) {
      this.value = String(v)
        .replace(/&lt;/g, "<").replace(/&gt;/g, ">")
        .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
        .replace(/&amp;/g, "&");
    },
    value: "",
  }),
};

const mod = new Function(src + "\n;return {readZip, docxExtract, htmlExtract, tagVal};")();

/* ------------------------------------------------------------ zip builder */
function buildZip(entries) {
  const chunks = [], central = [];
  let offset = 0;
  const enc = new TextEncoder();
  for (const { name, body, store } of entries) {
    const nameB = enc.encode(name);
    const raw = enc.encode(body);
    const data = store ? raw : deflateRawSync(raw);
    const method = store ? 0 : 8;

    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0);
    lh.writeUInt16LE(20, 4);
    lh.writeUInt16LE(method, 8);
    lh.writeUInt32LE(0, 14);            // crc32, not validated by the reader
    lh.writeUInt32LE(data.length, 18);
    lh.writeUInt32LE(raw.length, 22);
    lh.writeUInt16LE(nameB.length, 26);
    lh.writeUInt16LE(0, 28);
    chunks.push(lh, Buffer.from(nameB), Buffer.from(data));

    const cd = Buffer.alloc(46);
    cd.writeUInt32LE(0x02014b50, 0);
    cd.writeUInt16LE(20, 4);
    cd.writeUInt16LE(20, 6);
    cd.writeUInt16LE(method, 10);
    cd.writeUInt32LE(0, 16);
    cd.writeUInt32LE(data.length, 20);
    cd.writeUInt32LE(raw.length, 24);
    cd.writeUInt16LE(nameB.length, 28);
    cd.writeUInt32LE(offset, 42);
    central.push(cd, Buffer.from(nameB));

    offset += lh.length + nameB.length + data.length;
  }
  const cdBuf = Buffer.concat(central);
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0);
  eocd.writeUInt16LE(entries.length, 8);
  eocd.writeUInt16LE(entries.length, 10);
  eocd.writeUInt32LE(cdBuf.length, 12);
  eocd.writeUInt32LE(offset, 16);
  const all = Buffer.concat([...chunks, cdBuf, eocd]);
  return all.buffer.slice(all.byteOffset, all.byteOffset + all.byteLength);
}

const DOC_XML = `<?xml version="1.0"?><w:document xmlns:w="x"><w:body>
<w:p><w:r><w:t>The kiln cooled too fast</w:t></w:r><w:r><w:t xml:space="preserve"> and the glaze crazed.</w:t></w:r></w:p>
<w:p><w:r><w:t>I timed the second firing</w:t></w:r><w:tab/><w:r><w:t>against the first.</w:t></w:r></w:p>
<w:p><w:ins w:author="Someone"><w:r><w:t>An inserted clause.</w:t></w:r></w:ins></w:p>
<w:p><w:r><w:t>R &amp; D notes &lt;draft&gt;</w:t></w:r></w:p>
</w:body></w:document>`;

const CORE_XML = `<?xml version="1.0"?><cp:coreProperties xmlns:cp="x" xmlns:dc="y" xmlns:dcterms="z">
<dc:creator>Jane Potter</dc:creator><cp:lastModifiedBy>Marketing Dept</cp:lastModifiedBy>
<dc:title>Q3 Glaze Report</dc:title><cp:revision>17</cp:revision>
<dcterms:created>2026-01-02T09:14:00Z</dcterms:created></cp:coreProperties>`;

const APP_XML = `<?xml version="1.0"?><Properties><Company>Acme Ceramics Ltd</Company>
<Application>Microsoft Office Word</Application><TotalTime>438</TotalTime></Properties>`;

let pass = 0, fail = 0;
const log = [];
const pending = [];
// Every test registers a promise that is awaited at the end. An earlier version
// collected results under a setTimeout, which silently dropped any test slower than
// the timer: the decompression-bomb case inflates 40MB and vanished from the count,
// so the suite reported 11 passing on one run and 10 on the next without failing.
// A harness that quietly loses tests is worse than no harness.
function t(name, fn) {
  pending.push(
    Promise.resolve()
      .then(fn)
      .then(() => { pass++; log.push([name, "PASS", ""]); },
            (e) => { fail++; log.push([name, "FAIL", e.message]); })
  );
}
function eq(a, b, label) {
  if (a !== b) throw new Error(`${label || ""} expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`);
}
function ok(c, m) { if (!c) throw new Error(m); }
function metaHas(meta, key, val) {
  const row = meta.find((r) => r[0] === key);
  if (!row) throw new Error(`no metadata row ${key!==undefined?key:""} in [${meta.map((r) => r[0]).join(", ")}]`);
  if (val !== undefined && row[1] !== val) throw new Error(`${key}: expected ${val}, got ${row[1]}`);
}

const zip = buildZip([
  { name: "[Content_Types].xml", body: "<Types/>", store: true },
  { name: "word/document.xml", body: DOC_XML },
  { name: "docProps/core.xml", body: CORE_XML },
  { name: "docProps/app.xml", body: APP_XML },
  { name: "word/comments.xml", body: "<w:comments/>" },
]);

t("zip reader finds every entry, stored and deflated", async () => {
  const files = await mod.readZip(zip);
  ok(files.has("word/document.xml"), "missing document.xml");
  ok(files.has("[Content_Types].xml"), "missing the STORED entry");
  eq(files.size, 5, "entry count");
});

t("docx prose is extracted with paragraph breaks", async () => {
  const r = await mod.docxExtract(zip);
  ok(r.text.startsWith("The kiln cooled too fast and the glaze crazed."), "run joining is wrong: " + r.text.slice(0, 60));
  ok(r.text.includes("\n\n"), "paragraphs must be separated by a blank line");
  ok(!r.text.includes("<w:"), "xml tags leaked into the prose");
});

t("docx entities are unescaped", async () => {
  const r = await mod.docxExtract(zip);
  ok(r.text.includes("R & D notes <draft>"), "entities not decoded: " + JSON.stringify(r.text.slice(-40)));
});

t("docx tabs survive as tabs", async () => {
  const r = await mod.docxExtract(zip);
  ok(r.text.includes("\t"), "w:tab should become a tab character");
});

t("author, company and editing time are reported", async () => {
  const r = await mod.docxExtract(zip);
  metaHas(r.meta, "Author", "Jane Potter");
  metaHas(r.meta, "Last modified by", "Marketing Dept");
  metaHas(r.meta, "Company", "Acme Ceramics Ltd");
  metaHas(r.meta, "Revision number", "17");
  metaHas(r.meta, "Total editing time", "438 minutes");
  metaHas(r.meta, "Created", "2026-01-02T09:14:00Z");
});

t("tracked changes and comments are flagged", async () => {
  const r = await mod.docxExtract(zip);
  ok(r.extras.includes("tracked changes"), "w:ins should flag tracked changes");
  ok(r.extras.includes("reviewer comments"), "comments.xml should be flagged");
});

t("a non-docx buffer fails loudly rather than silently", async () => {
  let threw = false;
  try { await mod.docxExtract(new TextEncoder().encode("not a zip at all").buffer); }
  catch { threw = true; }
  ok(threw, "must throw on a file that is not a zip");
});

t("a zip without document.xml is rejected", async () => {
  const bad = buildZip([{ name: "hello.txt", body: "hi" }]);
  let threw = false;
  try { await mod.docxExtract(bad); } catch { threw = true; }
  ok(threw, "must reject a zip that is not a .docx");
});

t("a decompression bomb is refused rather than inflated", async () => {
  // ~40MB of zeroes compresses to a few KB. Without the guard this hangs the tab.
  const bomb = buildZip([
    { name: "word/document.xml", body: "<w:t>ok</w:t>" },
    { name: "docProps/core.xml", body: "<x>" + "0".repeat(40 * 1024 * 1024) + "</x>" },
  ]);
  let msg = "";
  try { await mod.docxExtract(bomb); } catch (e) { msg = e.message; }
  ok(/refusing to read it/.test(msg), "expected a refusal, got: " + (msg || "no error at all"));
});

t("non-document entries are never inflated", async () => {
  const withJunk = buildZip([
    { name: "word/document.xml", body: "<w:p><w:r><w:t>prose</w:t></w:r></w:p>" },
    { name: "word/media/huge.bin", body: "x".repeat(40 * 1024 * 1024) },
  ]);
  const r = await mod.docxExtract(withJunk);
  ok(r.text.includes("prose"), "prose should still come through");
});

t("html import reports author meta and comments", () => {
  const r = mod.htmlExtract(
    '<html><head><meta name="author" content="Jane Potter">' +
    '<meta name="generator" content="SomeCMS 4.2"></head><body>' +
    "<!-- internal: do not ship this line --><p>Real prose here.</p>" +
    '<p data-track="a" data-id="b">More prose.</p><script>var x=1;</script></body></html>'
  );
  metaHas(r.meta, "Meta author", "Jane Potter");
  metaHas(r.meta, "Meta generator", "SomeCMS 4.2");
  metaHas(r.meta, "HTML comment", "internal: do not ship this line");
  metaHas(r.meta, "data-* attributes", "2 removed");
  ok(r.text.includes("Real prose here."), "prose missing");
  ok(!r.text.includes("var x"), "script content leaked");
  ok(!r.text.includes("do not ship"), "comment leaked into prose");
});

const EXPECTED = 11;   // bump when you add a test; this is the drop-detector

await Promise.all(pending);
log.sort((a, b) => a[0].localeCompare(b[0]));
const w = Math.max(...log.map((l) => l[0].length));
for (const [n, s, m] of log) console.log(`${s.padEnd(5)} ${n.padEnd(w)}  ${m}`);
const counted = pass + fail;
console.log(`\n${pass} passed, ${fail} failed.`);
if (counted !== EXPECTED) {
  console.error(`HARNESS ERROR: ${counted} tests ran but ${EXPECTED} are registered. ` +
                `A test was dropped rather than failing.`);
  process.exit(1);
}
process.exit(fail ? 1 : 0);
