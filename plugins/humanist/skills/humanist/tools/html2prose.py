#!/usr/bin/env python3
"""html2prose.py - turn a CMS page/article body HTML into the markdown-ish
text superhumanizer.py expects.

  python3 html2prose.py body.html > body.txt

WHY THIS EXISTS. Check the source body HTML, not the rendered DOM. A rendered
page includes theme chrome (nav, footer, and promo widgets), and every one of
those strings becomes a prose false positive under a style sweep.
Reading the PAGE BODY instead of the rendered page removes the whole
false-positive class by construction: theme chrome is not page copy and never
enters the file.

  export body HTML from the CMS -> html2prose.py -> superhumanizer.py

Mapping, so the rules that need structure can fire:
  script/style/noscript  -> dropped entirely (structured data is not prose)
  h1..h6                 -> '#'*n + ' ' + text   (heading rules need this)
  blockquote             -> '> ' lines           (so --strip-quotes works)
  li                     -> '- ' + text
  everything else        -> one block per line, blank line between

IT PRINTS ITS OWN ELEMENT COUNTS TO STDERR, so a partial extraction can never
be reported as a full one.
"""
import re, sys, html as ihtml

if len(sys.argv) < 2:
    sys.exit("usage: python3 html2prose.py body.html > body.txt")
RAW = open(sys.argv[1], encoding="utf-8").read()
n_script = len(re.findall(r"<script\b", RAW, re.I))
n_pre = len(re.findall(r"<pre\b", RAW, re.I))
body_nopre = re.sub(r"<pre\b.*?</pre>", "", RAW, flags=re.S | re.I)
body = re.sub(r"<(script|style|noscript)\b.*?</\1>", "", body_nopre, flags=re.S | re.I)
BLOCK = r"<(h[1-6]|p|li|figcaption|blockquote|th|td|caption)\b[^>]*>(.*?)</\1>"

def detag(s):
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", ihtml.unescape(s)).strip()

out, counts = [], {}
for m in re.finditer(BLOCK, body, re.S | re.I):
    tag, inner = m.group(1).lower(), m.group(2)
    if tag == "blockquote":
        for pm in re.finditer(r"<p\b[^>]*>(.*?)</p>", inner, re.S | re.I):
            t = detag(pm.group(1))
            if t:
                out.append("> " + t)
        counts["blockquote"] = counts.get("blockquote", 0) + 1
        out.append("")
        continue
    t = detag(inner)
    counts[tag] = counts.get(tag, 0) + 1
    if not t:
        continue
    if tag.startswith("h"):
        out.append("#" * int(tag[1]) + " " + t)
    elif tag == "li":
        out.append("- " + t)
    else:
        out.append(t)
    out.append("")

sys.stderr.write(
    "html2prose: %d script/style block(s) dropped; %d <pre> block(s) EXCLUDED BY DESIGN "
    "(source code is not prose); elements kept: %s\n"
    % (n_script, n_pre, ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
)
print("\n".join(out))
