# humanist

Write prose that reads as though a person wrote it, then check it mechanically.

Three stages, in order:

1. **The rewrite pass.** Siqi Chen's MIT-licensed
   [humanizer](https://github.com/blader/humanizer), vendored under
   `plugins/humanist/skills/humanist/third_party/`. It strips AI writing tells and
   rewrites rather than deletes.
2. **The checker.** `humanist.py`, a stdlib-only sweep over the trope inventory in
   `ai-tropes.md`. It reports FAIL and WARN counts, Flesch-Kincaid readability,
   anaphora runs, duplicate sentences and bold-bullet counts. **It never edits.**
3. **The composition read.** Five tells are manual forever, because no regular
   expression catches them without lying about its precision: dead metaphor,
   fractal summaries, analogy stacking, one-point dilution, near-verbatim
   repetition.

The pass rewrites, the checker measures, the read catches what regexes cannot see.
A rewrite is itself machine output and can reintroduce the tells it removes, so no
model grading its own prose is evidence of anything. The checker is dumb and
disinterested, which is what makes its zero mean something.

## What it does not do

**It does not detect AI text.** Nothing here can tell you whether a machine wrote a
passage. Tools that claim to are unreliable, and a false accusation is worse than
an unanswered question.

**It does not defeat AI detectors.** Statistical watermarking lives in word choice
across a whole passage, not in characters or phrases. Rewriting perturbs that
signal incidentally and nobody here can tell you by how much. The goal is prose
that is good and yours; reading as human is a consequence of that, not a trick
layered on top.

## Install

As a Claude Code plugin:

```bash
/plugin marketplace add itsryanlenk/humanist
/plugin install humanist@humanist
```

Or just clone it. Python 3.9+, standard library only, nothing to install.

```bash
git clone https://github.com/itsryanlenk/humanist
cd humanist
python scripts/validate_repo.py
```

## Quickstart

```bash
cd plugins/humanist/skills/humanist

python humanist.py draft.md                    # the checker
python humanist.py draft.md --strip-quotes     # drafts quoting primary sources
python humanist.py draft.md --lenient          # internal docs: register rules become notes
python humanist.py --rules                     # every rule ID, severity and register
python humanist.py draft.md --json             # machine-readable output

# web copy: check the source body, never the rendered DOM
python tools/html2prose.py body.html > body.txt
python humanist.py body.txt --strip-quotes

# calibrate voice bands from your own published writing
python humanist.py --calibrate my-writing/ --register general
python humanist.py draft.md --mode post --register general
```

FAIL does not ship in public copy and sets exit 1. WARN is judged in context and
counted. Exit 2 means the tool could not do its job, and is never a verdict.

## What the numbers say

This repository was built from an earlier tool and a full audit of it. Both the
audit and the recalibration it drove are reproducible from what is committed here.

**The checker leaves human prose alone.** Swept over 24 known-human documents
(107,191 words, published 1854 to 2018, four registers: public-domain literature,
US government works, IETF RFCs):

|                                 | previous rule set | this one            |
| ------------------------------- | ----------------- | ------------------- |
| FAILs raised                    | 919               | **8**               |
| FAILs per 1,000 words           | 8.57              | **0.07**            |
| Documents blocked               | 22 of 24 (91.7%)  | **4 of 24 (16.7%)** |
| Share from two typography rules | 94.6%             | 0%                  |

`tests/fp_guard.py` holds that line as a CI gate. Any rule change that pushes the
false-positive rate back up fails the build.

**And it still separates machine prose from human prose.** Over an independent
corpus of 73 passages across six registers and three lengths:

| arm                          | FAIL per 1k | documents blocked |
| ---------------------------- | ----------- | ----------------- |
| raw AI draft                 | 1.02        | 9 of 18           |
| after the rewrite pass       | 0.50        | 4 of 18           |
| after fixing the FAILs       | 0.00        | 0 of 18           |
| genuine pre-2021 human prose | 0.00        | 0 of 19           |

Two independent human corpora, both at zero. That is the property that makes the
number worth reading.

**But a blind reader still tells the difference.** In a separate study of 576
judgments over 282 blinded passages, judges were shown one passage at a time with
no context and asked whether a person or a machine wrote it:

| arm                          | called machine-written |
| ---------------------------- | ---------------------- |
| raw AI draft                 | 100.0%                 |
| after the rewrite pass       | 98.6%                  |
| after the checker was clean  | **97.8%**              |
| genuine pre-2021 human prose | **0.0%**               |

The judge was right about human prose 143 times out of 143, at mean confidence
4.95 of 5, with cross-pass agreement of 0.946. The instrument is not blunt, it is
**saturated**: pinned to 0% on one rail and 98.8% on the other, with no dynamic
range left. The honest statement is **no effect detected**, not an effect of 2.2
points, because the design could not resolve anything below about 3.6 points.

The reason is the most useful thing measured here: the pipeline crushes every tell
it encodes and _grows_ the ones it does not. AI vocabulary went 70 citations to 0;
uniform beat rate went 60 to 101, and aphoristic closers 38 to 61. A subtractive
rewrite makes prose more uniformly well-shaped, and uniform good shape is itself
the tell. Ten named tells have no rule at all, and every one is rhythmic or
structural while the checker is almost entirely lexical.

One caution carried over from the same study: **performed hedging looks like a
tell and is not one.** Judges cited it 137 times as machine evidence and 50 times
as human evidence, so a rule built on it would fire on careful human writing. The
same test is why em dashes and curly quotes are WARN rather than FAIL here.

See [docs/evals/](docs/evals/README.md) for the design, the cross-tabs and the
caveats, and `ai-tropes.md` under "The rhythm tells" for what to do about it.

### Why the previous defaults were wrong

94.6% of the old rule set's failures came from two rules, curly quotes and em
dashes, which describe how a file was encoded rather than how it was written. Jack
London's chapter scored 199 failures, all 199 of them quotes and dashes. Both now
default to WARN.

Two more rules were demoted against evidence:

- **AI vocabulary** split into two tiers. All 15 of its hits on the human corpus
  were ordinary English: Obergefell's "fostered and then adopted a baby boy," the
  Rogers Commission's "crucial information about the O-ring damage," Thoreau's
  "elevate his life," RFC 793's "utilize the SYN control flag." A small anchored
  FAIL tier survives for constructions with no innocent use.
- **Negative parallelism** became a counted WARN. Its detection was _widened_ (it
  used to miss three of the five forms its own name claimed) but 10 of its 17
  corpus hits were the correlative "not only X but Y" as written by Thoreau, Du
  Bois, Russell, and by Strunk in _Elements of Style_.

Six correctness defects were fixed in the same pass, each now a regression test in
`tests/test_humanist.py`:

- A curly apostrophe defeated 12 of 41 rules, and the project's own HTML extractor
  produces curly apostrophes by design, so the documented web-copy workflow
  defeated the checker.
- A UTF-8 BOM (what PowerShell 5.1 writes by default) silently disabled every
  line-anchored rule on the first line.
- The unicode-arrow rule crashed the reporter on a Windows console. The one rule
  whose purpose is catching arrows was the rule that killed the process when it
  fired, and through the documented pipeline that crash printed `CLEAN` on a
  zero-byte file.
- `severity_overrides` matched rule names by substring, so a key of `often`
  silently disabled an unrelated rule. Keys are now exact rule IDs, and an unknown
  one is a hard error.
- `--calibrate` overwrote an unparseable config behind a success message,
  destroying the only persistent state the tool has.
- Readability targets were printed next to the word "gate" and compared against
  nothing, so a draft at grade 38 exited clean.

## Inkwash

`app/inkwash.html` is a single offline page that strips invisible characters and
machine typography out of finished prose: zero-width characters, smuggled Unicode
tag payloads (which it decodes and shows you), homoglyph letters borrowed from
Cyrillic and Greek, bidirectional controls, deprecated and interlinear-annotation
controls, exotic spaces, curly quotes, en and em dashes. Every change is itemized
with its codepoint and surrounding text.

Coverage is audited rather than asserted: every Unicode format, space and separator
character is enumerated and probed against the engine, and the only one deliberately
left alone is U+0020.

It also reads **.docx and .html** and reports the metadata inside them, which is the
part people forget. A Word file carries the author's name, the company, the revision
count and the total editing time; an HTML export carries generator tags and whatever
the CMS left in comments. None of that is in the prose, so washing cannot touch it,
so Inkwash shows you what was there and hands you clean text that leaves it behind.

The .docx reader is a hand-written ZIP parser, so it only inflates the four entries a
.docx keeps prose and metadata in, and it refuses any archive that inflates past a
size cap. `app/test-docx.mjs` builds real ZIPs byte-for-byte to test it, including a
decompression bomb.

Open the file. There is no build step, no server, no network request, and no
dependency. Text pasted into it never leaves the machine.

It works on characters, so it cannot touch a statistical watermark, and it says so
on the page rather than in the footnotes. Emoji sequences and genuine non-Latin
text survive it untouched, which is what most of `app/test-inkwash.mjs` is about.

## Layout

```
plugins/humanist/skills/humanist/
    SKILL.md              the pipeline orchestrator
    humanist.py           the checker and calibration
    ai-tropes.md          the negative list it encodes
    config.example.json   worked configuration examples
    tools/html2prose.py   CMS body HTML to checker-ready text
    third_party/humanizer/  the rewrite pass, vendored (MIT + CC BY-SA, see below)
app/
    inkwash.html          the sanitizer, single file, offline
    test-inkwash.mjs      31 engine tests
tests/
    test_humanist.py      41 regression tests, one per fixed defect
    fp_guard.py           the false-positive CI gate
    fp-corpus/            24 human documents with full provenance
scripts/validate_repo.py  structure, manifests, references, privacy, spelling
docs/attribution.md       the full third-party inventory
```

## Configuration

House taste is config, never core. Copy `config.example.json` to
`humanist.config.json` or pass `--config`. Voice bands are not shipped at all: they
are meaningless until measured from the actual author, so you generate your own
with `--calibrate` from writing you published to an audience, unassisted.

`humanist.config.json` is gitignored. It records the filenames it measured, and
those are yours.

## License and credits

MIT for this repository's own work; see `LICENSE`.

Two carve-outs, because parts of this tree are not ours to relicense:

- `third_party/humanizer/` keeps Siqi Chen's MIT license and copyright. **Its
  pattern catalog is additionally subject to
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)**, because 27.5%
  of it is verbatim text from Wikipedia's
  [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
  (maintained by WikiProject AI Cleanup). ShareAlike travels with that material and
  MIT cannot satisfy it.
- The trope taxonomy in `ai-tropes.md` is seeded from
  [tropes.fyi](https://tropes.fyi) by ossama.is, which states no license.

`docs/attribution.md` has the full inventory, the measurement method and the
per-section overlap table. Names are used descriptively; this project is not
affiliated with or endorsed by any of them.

## Honest caveats

- **The false-positive corpus skews formal and old.** It is heavy on pre-1920
  literature, so it under-samples contemporary conversational writing. It is
  evidence about one slice of human prose, not all of it.
- **The audit behind these numbers was self-graded.** Its auditors, its adversarial
  verifiers and its synthesis were all agents from one model family. The verifiers
  refuted 4 findings and downgraded 9 of 21, which is evidence the check had teeth,
  but it is not an independent check. A human reviewer is the right next step.
- **93 further findings were filed and never adversarially verified.** On the
  observed base rate, expect roughly a third of them to be over-rated.
- **25 of the shipped rules never fired on the false-positive corpus**, so their
  false-positive rate is unmeasured. A zero for those rules is evidence of nothing.
