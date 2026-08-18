# humanist

**Make an AI-assisted draft measurably better to read.** In a blind study, editors
preferred the processed draft over the raw one **22 times out of 22**.

That is the claim, and it is the only one this repository makes. It does not make
writing pass as human, it cannot defeat AI detection, and the studies in
[docs/evals/](docs/evals/README.md) are the reason both of those sentences are here
rather than in a footnote.

## What it is

**The rewrite pass.** Siqi Chen's MIT-licensed
[humanizer](https://github.com/blader/humanizer), vendored under
`plugins/humanist/skills/humanist/third_party/`. It strips inflated significance,
AI vocabulary, negative parallelisms, filler and fake-candid openers, rewriting
rather than deleting. **This stage carries the measured benefit: 16 of 16 blind
trials against the raw draft.**

**The checker.** `humanist.py`, a stdlib-only sweep over the trope inventory in
`ai-tropes.md`. It reports FAIL and WARN counts, readability, anaphora runs,
duplicate sentences and bold-bullet counts, and **it never edits**. Read the
[honest note on this stage](#the-checker-stage-is-not-proven) before relying on it.

**The composition read.** Five tells stay manual forever, because no regular
expression catches them without lying about its precision: dead metaphor, fractal
summaries, analogy stacking, one-point dilution, near-verbatim repetition.

## Install

```bash
/plugin marketplace add itsryanlenk/humanist
/plugin install humanist@humanist
```

Or clone it. Python 3.9+, standard library only, nothing to install.

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

# calibrate voice bands from your own published writing
python humanist.py --calibrate my-writing/ --register general
python humanist.py draft.md --mode post --register general
```

FAIL does not ship in public copy and sets exit 1. WARN is judged in context and
counted. Exit 2 means the tool could not do its job, and is never a verdict.

## What the studies say

Roughly 750 blind judgments across four designs. Everything below is reproducible
from what is committed here, including the results that went against the project.

### It makes prose better

Editors, told nothing about authorship and asked only which passage was the better
piece of writing:

| contrast                         | preferred | n   | p          |
| -------------------------------- | --------- | --- | ---------- |
| **raw draft vs fully processed** | **100%**  | 22  | 4.8 × 10⁻⁷ |
| raw draft vs rewrite pass only   | **100%**  | 16  | 3.1 × 10⁻⁵ |
| rewrite pass vs full pipeline    | 57%       | 21  | 0.66       |

Every register, every length. Zero coin-flip margins in the headline contrast.

### The checker stage is not proven

That third row is the honest part. **In 11 of 18 cells the checker emitted its input
byte-identical** — it declined to act 61% of the time, and twelve of the twenty-one
trials in that contrast were judges comparing a file to itself. Where it did act,
the edits were single clauses, and the resulting 7-of-9 preference cannot be
separated from chance at this n.

So: the rewrite pass earns its keep decisively. The checker is **not established to
help and not established to hurt.** It is shipped because a reporting pass that
never edits is cheap and its output feeds the composition read, not because a
measurement says it improves prose. If that bothers you, run the rewrite pass alone;
the evidence supports that.

### It does not make writing pass as human

| arm                         | called machine-written by a blind judge |
| --------------------------- | --------------------------------------- |
| raw AI draft                | 100.0%                                  |
| after the rewrite pass      | 98.6%                                   |
| after the checker was clean | **97.8%**                               |
| genuine human prose         | **0.0%**                                |

**No effect detected**, against a design that could not resolve anything below about
3.6 points. Explicit rules for "writing more human" fooled **0 of 17** judges.
Presenting the same text whole versus in ~500-word slices changed nothing.

The reason is the useful part: **the pipeline crushes every tell it encodes and
grows the ones it does not.** AI vocabulary fell from 70 judge citations to 0 while
uniform beat rate rose from 60 to 101 and aphoristic closers from 38 to 61. A
subtractive rewrite makes prose more uniformly well-shaped, and uniform good shape
is itself the tell. Ten named tells have no rule at all, and every one is rhythmic
rather than lexical.

### The finding that reframed the project

On the same corpus, processed machine prose beat genuine human prose **18 of 18** on
quality (rubric 87.1 vs 64.6; "would keep reading" 97.4% vs 42.9%) — while those
same human passages were identified as human **143 times out of 143**.

"Reads as human" and "is good writing" behaved as separable, in this corpus
anti-correlated, properties. **The caveat travels with the claim:** the human arm is
found text matched on register and length but _not subject_, so it is suggestive
rather than settled. [docs/evals/](docs/evals/README.md) states it the same way.

### It leaves human prose alone

Swept over 24 known-human documents (107,191 words, 1854–2018: public-domain
literature, US government works, IETF RFCs), the checker raises 8 failures — 0.07
per 1,000 words — and blocks 4 of 24. Raw AI drafts score 1.02 FAIL/1k against
0.00 for human prose across two independent corpora.

`tests/fp_guard.py` holds that as a CI gate. Rules were demoted against evidence,
never taste: typography defaults to WARN because two rules produced 94.6% of all
failures on human prose and 869 of 869 adjudicated false positives; AI vocabulary
split into two tiers after every one of its hits turned out to be ordinary English;
negative parallelism became a counted WARN after 10 of its 17 hits were the
correlative "not only X but Y" as written by Thoreau, Du Bois, Russell and Strunk.

## Inkwash

`app/inkwash.html` is a single offline page that strips invisible characters and
machine typography from finished prose and itemizes every change with its codepoint
and context. Open the file. No build step, no server, no network request, no
dependency; nothing you paste leaves the browser.

Coverage is audited rather than asserted: all 205 Unicode format, space and
separator codepoints are enumerated and probed, and the only one deliberately
untouched is U+0020. It is script-aware, so Arabic end-of-ayah marks, the Syriac
abbreviation mark, Egyptian hieroglyph controls, emoji ZWJ sequences and genuine
Cyrillic and Greek words survive intact. It decodes smuggled Unicode tag payloads
and shows them rather than silently deleting them.

It also reads **.docx and .html** and reports the metadata inside — author, company,
revision count, total editing time, tracked changes, reviewer comments. None of that
is in the prose, so washing cannot touch it; it is shown so you know what was riding
along, and the clean text leaves it behind. The .docx reader is a hand-written ZIP
parser tested against real archives built byte-for-byte, and hardened against
decompression bombs.

It works on characters, so it cannot touch a statistical watermark, and it says so
on the page rather than in the footnotes.

## Layout

```
plugins/humanist/skills/humanist/
    SKILL.md              the pipeline orchestrator
    humanist.py           the checker and calibration
    ai-tropes.md          the trope inventory, including the rhythm tells
    config.example.json   worked configuration examples
    tools/html2prose.py   CMS body HTML to checker-ready text
    third_party/humanizer/  the rewrite pass, vendored (MIT + CC BY-SA, see below)
app/
    inkwash.html          the sanitizer, single file, offline
    test-inkwash.mjs      39 engine tests
    test-docx.mjs         11 document-import tests
tests/
    test_humanist.py      43 regression tests, one per fixed defect
    fp_guard.py           the false-positive CI gate
    fp-corpus/            24 human documents with full provenance
scripts/validate_repo.py  structure, manifests, references, privacy, spelling
docs/evals/               the studies, including the negative results
docs/attribution.md       the full third-party inventory
```

## Configuration

House taste is config, never core. Copy `config.example.json` to
`humanist.config.json` or pass `--config`. Voice bands are not shipped: they are
meaningless until measured from the actual author, so you generate your own with
`--calibrate` from writing you published to an audience, unassisted.

`humanist.config.json` is gitignored. It records the filenames it measured, and
those are yours.

## License and credits

MIT for this repository's own work; see `LICENSE`. Two carve-outs, because parts of
this tree are not ours to relicense:

- `third_party/humanizer/` keeps Siqi Chen's MIT license and copyright. **Its
  pattern catalog is additionally subject to
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)**, because 27.5%
  of it is verbatim text from Wikipedia's
  [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
  ShareAlike travels with that material and MIT cannot satisfy it.
- The trope taxonomy in `ai-tropes.md` is seeded from
  [tropes.fyi](https://tropes.fyi) by ossama.is, which states no license.

`docs/attribution.md` has the inventory, the measurement method and the per-section
overlap table. Names are used descriptively; this project is not affiliated with or
endorsed by any of them.

## Honest caveats

- **Judges and prose come from one model family.** An editor model preferring a
  passage is not a human reader preferring it. This is the largest limitation and it
  bounds every number above.
- **The quality study ran short.** 54 of 144 planned pairwise trials were judged
  after agent failures. Direction is unambiguous; the ceiling is not pinned.
- **The false-positive corpus skews formal and old**, heavy on pre-1920 literature.
  It is evidence about one slice of human prose, not all of it.
- **93 audit findings were filed and never adversarially verified.** On the observed
  base rate, expect roughly a third to be over-rated.
- **25 of the shipped rules never fired on the false-positive corpus**, so their
  false-positive rate is unmeasured. A zero for those rules is evidence of nothing.
