---
name: humanist
description: |
  Improve an AI-assisted draft so it reads better: strip machine residue, cut
  filler and inflated significance, and report what is left. Use when someone
  wants to clean up an AI-assisted draft, edit AI output into publishable prose,
  remove AI slop, fix corporate or robotic voice, tighten a draft before it ships,
  or asks why their writing sounds generic. Trigger phrases include "clean up this
  AI draft", "edit this into something publishable", "remove the AI slop", "this
  reads like ChatGPT wrote it", "why does this sound robotic", "tighten this before
  it goes live", "make this draft less generic". Runs a rewrite pass, a mechanical
  checker that reports and never edits, and a composition read for the tells no
  regular expression catches. Also covers quoted sources, web-copy extraction, and
  calibrating the checker to the author's own published voice. It does NOT detect
  whether text was AI-generated, does NOT make writing pass as human, and does NOT
  defeat AI-detection or watermarking.
---

# Humanist: edit the draft, then read it

**The goal is a better piece of writing, not a disguised one.** In a blind study
where editors judged quality alone, the processed draft beat the raw draft 22 times
out of 22. In a separate study, the same processing moved detection of machine
authorship by no measurable amount. Both of those are true at once, and the first
is the one worth working for.

So the work splits into a pass that **rewrites**, a checker that **reports**, and a
read that catches what no regular expression will. Run them in that order, and read
the note on what each stage is actually known to do.

**Before anything else, name the surface.** Public long-form, internal document,
short-form social, quotable snippet. The `--lenient` flag, the readability targets
and the calibration bands all differ by register, and a draft judged against the
wrong one produces confident nonsense in both directions.

## What this does not do

Three non-goals. The first two are impossible here; the third was attempted,
measured, and abandoned.

**It does not detect AI text.** Given a passage, this skill cannot tell you whether
a machine wrote it. Nothing in the repository does that, the accuracy of tools that
claim to is poor, and a false accusation is worse than an unanswered question.

**It does not defeat AI detection or watermarking.** Statistical watermarks live in
word choice across a whole passage, not in characters or phrases, and no rewrite can
promise anything about them.

**It does not make prose pass as human, and that was the original goal.** Across
roughly 700 blind judgments: raw output was identified as machine-written 100% of
the time and fully processed output 97.8%, a difference smaller than the design
could resolve. Explicit instructions for "writing more human" fooled 0 of 17 judges.
Length changed nothing. Genuine human prose was never once misidentified.

The reason is worth carrying into the work: **the pipeline removes the tells it
encodes and worsens the ones it does not.** AI vocabulary fell from 70 judge
citations to zero while uniform beat rate rose from 60 to 101. A subtractive rewrite
makes prose more uniformly well-shaped, and uniform good shape is itself a tell. If
you want prose that reads as a person's, that comes from the person: the specifics
only they hold, unevenly distributed, with the rough parts left in. A pipeline cannot
supply it, and step 3 below is where it has to enter.

## The pipeline

### Step 1: the rewrite pass

Read `third_party/humanizer/SKILL.md` in full and apply it. It is Siqi Chen's
MIT-licensed humanizer, vendored here, and it is the subtractive half: it strips
inflated significance, AI vocabulary, negative parallelisms, filler, fake-candid
openers and the rest of its 33 patterns, rewriting rather than deleting.

Skipping this wastes everything after it, because the checker would drown in
findings that one rewrite clears wholesale.

Two cautions the pipeline's own audit surfaced:

- **Do not swap an em dash for a spaced hyphen and consider it handled.** That
  produces a construction the composition read then has to catch. An em dash
  usually wants the sentence rebuilt around it.
- **The rewrite pass is itself machine output.** Everything it produces goes
  through step 2. That is the entire reason step 2 exists.

### Step 2: the checker

```bash
python humanist.py draft.md
```

It sweeps the draft against the rules derived from `ai-tropes.md`, unwraps soft
line breaks first (a hard-wrapped draft otherwise defeats every multi-word
pattern), and reports counts. **It never edits.**

Read the frame it prints before the findings. It states the word count, which
config it loaded, how many of its rules are active, how many were overridden, and
the readability grade. A run with rules silenced cannot masquerade as a clean
sweep, which is the point.

**Severity.** FAIL does not ship in public copy and sets exit 1. WARN is judged in
context and counted, so repetition stays visible. `--lenient` downgrades the format
and phrasing registers to notes for internal documents, which legitimately use bold
bullets and plainer hedging on purpose.

**Read WARN counts as density, not as a list of errors.** For the largest family of
tells, the not-X-but-Y antithesis above all, any single instance is usually fine
and the pattern is what gives a draft away. One is nothing. Six in eight hundred
words is the tell.

**Exit codes.** 0 clean, 1 FAILs remain, 2 the tool could not do its job. Never
treat 2 as a verdict; it means the run did not happen.

**What this stage is known to do, honestly.** In a blind quality study the rewrite
pass beat the raw draft 16 of 16 times. Adding this checker on top of it produced no
measurable further gain: it changed nothing at all in 11 of 18 cells, and where it
did act the preference could not be separated from chance. Treat its output as
**material for the composition read**, which is what it is good for, rather than as
a stage that improves the draft on its own. Its clean report is not evidence the
prose is finished.

### Step 3: the composition read

Five tells are manual forever, because no regular expression catches them without
lying about its precision. After the checker is clean, read the piece aloud:

1. **Dead metaphor.** One metaphor beaten five to ten times. Introduce it, use it,
   move on.
2. **Fractal summaries.** Summaries of summaries at every level. One close per
   piece.
3. **Analogy stacking.** Rapid-fire borrowed authority. Your own receipts outrank
   anyone else's.
4. **One-point dilution.** One argument restated ten ways to feel thorough. State
   the conclusion once and end there. A case that takes 800 words gets 800 words.
5. **Near-verbatim repetition.** Exact repeats are caught mechanically; the
   near-verbatim kind needs the read.

Then check the five laws below at paragraph scale. Drafts scoring zero FAILs have
still contained tells found only on a read-aloud. **The read makes the final call.**
The checker exists to make the read cheaper, never to replace it.

**This step carries more weight than the two before it.** The measured tells that
survive a clean checker run are all rhythmic and structural rather than lexical, and
`ai-tropes.md` has them under "The rhythm tells" with what to do about each. The
short version: vary paragraph length so no two land the same number of beats, end
half your sections flat rather than on an epigram, hedge only where the writer would
genuinely be unsure, leave one objection standing, and put in the specifics only the
author has. None of that is checkable by machine, all of it is what a reader
notices, and the author has to supply it.

## The five laws

The deepest family of tells is a sentence _about_ the material instead of the
material. Each instance is well-formed English, which is why surface rules miss it.

1. No sentence may justify a choice the page has already made.
2. No sentence may announce the writer's own honesty. Admitting a concrete fault is
   fine; it costs the writer something. Cut any line that compliments its own
   candor.
3. No sentence may tell the reader how to weigh material it has not shown yet.
4. No phrase may assert that the material deserves the reader's attention.
5. The page does not manage the reader's verdict. It supplies material, not
   conclusions about the material. This one subsumes the other four.

## Quoted sources

```bash
python humanist.py draft.md --strip-quotes
```

The checker cannot tell your prose from a source you quote, and a quoted source
will happily trip style rules its author never agreed to. `--strip-quotes` removes
blockquote lines before scoring and prints how many. Run it on anything carrying
quoted material, and remember why it exists: a quoted source is evidence, and
editing evidence to satisfy a style rule is falsifying it.

## Web copy

Never run the checker on raw HTML or on text scraped from a rendered page. The
rendered DOM carries theme chrome (nav, footer, promo widgets), and every one of
those strings is a false positive. Export the body HTML from the CMS instead:

```bash
python tools/html2prose.py body.html > body.txt
python humanist.py body.txt --strip-quotes
```

`html2prose.py` maps headings to `#`, blockquotes to `>`, list items to `-`,
excludes code blocks by design, and prints its element counts to stderr so a
partial extraction cannot be reported as a full one.

## Calibration

Out of the box the checker runs its universal rules against wide generic bands
labeled UNCALIBRATED. Voice bands are meaningless until measured from the actual
author.

```bash
python humanist.py --calibrate my-writing/ --register general
python humanist.py draft.md --mode post --register general
```

Point `--calibrate` at a directory of your own `.md`/`.txt` writing. Each run pools
that directory into one corpus and produces one band set stored under `--register`,
written to `humanist.config.json` in the current directory. Multiple registers are
multiple named band sets: run it once per register, each on its own directory. A
technical how-to and a first-person essay are different measurements and differ
more than the markers do.

**The sampling law, binding.** A rare-event rate cannot be tested below the word
count that yields an expected count of about three. Below that the checker prints
UNTESTABLE instead of a number. A marker rate from a short piece is noise in both
directions: do not report it, and do not let a clean short sample count as evidence
the voice landed.

**Calibration pitfall.** Measure published writing, not chat logs. Collaborator and
chat corpora over-predict first person and question rate, because collaborating
inflates both. Calibrate on what you shipped to an audience, unassisted.

## Configuration

House taste is config, never core. `config.example.json` documents each key with
worked examples; copy it to `humanist.config.json` or pass `--config`.

- **`severity_overrides`.** Keys are rule IDs, matched **exactly**. Run
  `python humanist.py --rules` for the list. An unknown ID or an invalid severity
  is a hard error rather than a silent no-op, because the previous behavior turned
  a FAIL into an uncounted note and let the run report CLEAN.
- **`extra_banned_words` / `extra_warn_words`.** Per-house bans with your own
  rationale. A blanket ban on a common English word is house taste, not universal
  law, which is why the shipped set contains none.
- **`never_flag_words` / `exempt_patterns`.** How a real author's measured tics
  survive the sweep. Exempt patterns are anchored at the hit, so an empty
  drum-roll still fails while an anchored report survives.
- **`fk_quotable` / `fk_body`.** Readability targets, checked and reported as a
  WARN. An audience-friction measure, not a voice measure: a real voice at grade 9
  beats slop at grade 6.

Two reconciliation tests generalize whenever a rule and a real sentence collide.
**Genuine questions survive**; only the self-answered drama form is a tell, and the
test is to flatten the question into a statement, and if nothing is lost it was
staging. **Literal industry senses survive**; a platform ecosystem and a software
framework are legitimate, and abstract use is the offense.

## Why the defaults are calibrated the way they are

The rule set this skill inherited was swept over 24 known-human documents (107,191
words, published 1854 to 2018, across four registers) and **blocked 22 of them.**
94.6% of its 919 failures came from two rules, curly quotes and em dashes, which
describe how a file was encoded rather than how it was written. Jack London's
chapter scored 199 failures, all 199 of them quotes and dashes.

After recalibration the same corpus produces **8 failures and blocks 4 documents.**
Every rule that was demoted was demoted against evidence, not taste:

- **AI vocabulary** split into two tiers. Every one of its 15 hits on the human
  corpus was ordinary English: Obergefell's "fostered and then adopted a baby
  boy," the Rogers Commission's "crucial information about the O-ring damage,"
  Thoreau's "elevate his life," RFC 793's "utilize the SYN control flag." A small
  anchored FAIL tier remains for constructions with no innocent use.
- **Negative parallelism** became a counted WARN. Its detection was _widened_, since it
  used to miss three of the five forms its own name claimed, but 10 of its 17
  corpus hits were the correlative "not only X but Y" as written by Thoreau, Du
  Bois, Russell, and by Strunk in _Elements of Style_.

This matters for how you read the output. A checker that fails nine of ten
published essays does not measure what it claims to, and its users learn to ignore
the number. `tests/fp_guard.py` is a CI gate that holds this line: any rule change
pushing the false-positive rate back up fails the build.

## The honesty rule

**The checker never edits. It only reports. The person decides.** Every fix is made
by the author or with the author's sign-off, because a checker that rewrites is a
checker that can falsify without leaving a trace.

Standing corollaries:

- Never soften a claim to make it flow. Every number keeps its source and its base.
- Never add a story, an example, or a number the author did not supply. Leave
  `[AUTHOR: ...]` placeholders until they fill them.
- The medium decides length. When a register is uncalibrated, shorter is the safer
  error for anything public.
- A rule change is not an implementation fix. Widening a regex so it matches its
  own stated law is maintenance; changing the law is a decision. Both get swept
  over the false-positive corpus before they ship.
- What makes prose attributable is its specifics. Strip them and the line could
  have come from anyone. What cannot be faked is the evidence only you hold: the
  events you witnessed, the numbers whose denominators you can produce. This is the
  one input no stage of this pipeline can generate, and the measurements say it is
  the input that matters most.

## Companion tool

`app/inkwash.html` at the repository root is a single offline page that strips
invisible characters and machine typography out of finished prose, and reports the
metadata hiding inside imported .docx and .html files: zero-width
characters, smuggled Unicode tag payloads, homoglyphs, exotic spaces, curly quotes.
It runs entirely in the browser and reports every change it makes. It works on
characters, so it cannot touch a statistical watermark, and it says so on the page.
