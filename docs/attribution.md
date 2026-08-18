# Attribution and third-party licenses

This repository redistributes work by other people. This file is the complete
inventory of what, from where, and under which terms, so that anyone can check the
chain rather than take it on trust.

It exists because the version of this project that preceded it got this wrong. Its
entire license statement was "MIT for everything outside `third_party/`", and a
compliance audit found that description was incompatible with what the tree
actually contained. The details are in [§2](#2-wikipedias-signs-of-ai-writing-cc-by-sa-40),
because a correction that hides the thing it corrects is not a correction.

---

## The short version

| Component                            | Origin                          | License                        |
| ------------------------------------ | ------------------------------- | ------------------------------ |
| Everything not listed below          | This project                    | MIT (see `LICENSE`)            |
| `.../third_party/humanizer/`         | `blader/humanizer` by Siqi Chen | MIT                            |
| The pattern catalog inside it      | Wikipedia, via the above        | **CC BY-SA 4.0** (also)        |
| The trope taxonomy in `ai-tropes.md` | tropes.fyi by ossama.is         | **No license stated** — see §3 |

The MIT grant in `LICENSE` covers this project's own work. It does not and cannot
extend to §2 or §3.

---

## 1. The humanizer rewrite pass (MIT)

**Vendored at:** `plugins/humanist/skills/humanist/third_party/humanizer/`
**Upstream:** <https://github.com/blader/humanizer>
**Author:** Siqi Chen
**License:** MIT, `Copyright (c) 2025 Siqi Chen`

The upstream `LICENSE` is vendored unmodified alongside the work, which is what MIT
requires. It was verified byte-identical against upstream commit `9600f2b7241c`:

```
upstream bytes 1066   vendored bytes 1066   byte-identical: true
sha256 4ac4810254ab36d45419141aeb8e69bf50652cfafe5b2dab947d06d44e5cbf96
```

### Local modifications

The upstream `SKILL.md` ships with live YAML frontmatter. Vendoring it unchanged
causes a plugin loader to register it as a **second, independent skill** that can
load on its own — a rewrite pass with no gate behind it, which is precisely the
configuration this project argues against. Its frontmatter has therefore been
neutralized so the file is documentation rather than an installable skill.

That is the only change, it is recorded here as MIT requires, and the pattern
content itself is untouched.

---

## 2. Wikipedia's "Signs of AI writing" (CC BY-SA 4.0)

**Source:** <https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>
**Maintained by:** WikiProject AI Cleanup
**License:** [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/)

The vendored humanizer's pattern catalog is substantially derived from this page.
Upstream says so itself — its changelog entry for v2.0.0 reads _"Complete rewrite
based on raw Wikipedia article content."_

### How much, measured

An n-gram overlap harness comparing the vendored file against the Wikipedia
revision immediately preceding upstream's rewrite commit (rev `1333489114`,
2026-01-18) found every maximal verbatim run of six or more words after
normalization:

| Section of the vendored file                       | Lines   | Verbatim overlap |
| -------------------------------------------------- | ------- | ---------------- |
| Frontmatter, intro, voice calibration, personality | 1–87    | 0.0%             |
| **Pattern catalog, patterns 1–25**               | 88–415  | **28.4%**        |
| Patterns 26–33                                     | 417–522 | 0.0%             |
| Detection guidance                                 | 523–556 | 1.1%             |
| Process and worked example                         | 560–616 | 0.9%             |

The derivation is concentrated rather than diffuse, and the honest way to say that
is: the copied part is the part the skill is for. What was taken is Wikipedia's
selection of examples, its watch-word lists in their original order, its problem
statements, its section taxonomy heading-for-heading, and in one case its
distinctive bracket-and-slash notation. What was authored upstream is every
"After:" rewrite — those produced zero matches — plus patterns 26–33 and the
surrounding process.

### What that means for anyone using this repository

CC BY-SA 4.0 permits redistribution, including commercially. It attaches two
conditions, and both apply to the pattern catalog:

- **Attribution** (§3(a)): credit the source, link the license, indicate changes.
  That is what this section does.
- **ShareAlike** (§3(b)): distribute contributions built on that material under CC
  BY-SA 4.0 or a compatible license.

MIT is not on Creative Commons' compatible-license list and cannot be, because MIT
permits downstream relicensing with no copyleft carry-forward — exactly what
ShareAlike forbids. So the pattern catalog is **not** available to you under this
repository's MIT grant. If you copy that material onward, CC BY-SA 4.0 travels with
it.

Everything else in this repository — the checker, its rule set, the tooling,
Inkwash, and this project's own prose — is original work under MIT.

---

## 3. tropes.fyi (no license stated)

**Source:** <https://tropes.fyi>
**By:** ossama.is

The negative-trope taxonomy in `ai-tropes.md` is seeded from this site. A crawl of
the site root, its `robots.txt` and its linked gist found **no license statement of
any kind**. Absent a stated license, the default is ordinary copyright, so "seeded
from" describes a real dependency rather than a courtesy credit, and pretending
otherwise would be the kind of thing this project exists to object to.

What that means concretely: 25 of 35 trope **labels** in `ai-tropes.md` match
labels on tropes.fyi, and text overlap measured against the site's index payload is
5.9% — a lower bound, since per-trope detail pages were not crawled. The
explanatory prose, the reconciliation notes, the severity model and every
configuration example around those labels are this project's own.

Trope names are short factual labels used here as commentary on a shared
phenomenon. The MIT grant in `LICENSE` covers this repository's prose about that
taxonomy; it does not purport to license the taxonomy itself. If ossama.is would
prefer different treatment, that is a reasonable request and this project will
honor it — open an issue.

---

## 4. Names used descriptively

Product, project and organization names appear here to identify what is being
referred to. This project is not affiliated with, endorsed by, or sponsored by the
Wikimedia Foundation, WikiProject AI Cleanup, Anthropic, Google, or any other named
party. Trademarks belong to their owners.

---

## 5. If you think something here is wrong

Open an issue. An attribution error is a defect like any other, and this file was
written by the same process that found the last one.

_None of the above is legal advice. Every statement about what MIT and CC BY-SA 4.0
require is a reading of the license texts, cited by section; every statement about
what this repository contains is verifiable against the files themselves._
