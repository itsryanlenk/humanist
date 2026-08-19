<!-- The analyst's report, vendored verbatim apart from local paths scrubbed and
     spelling normalized. No number or judgment was altered. This is the authority
     where it and any summary disagree. -->

# Does the processed prose actually read better?

**Lab:** `<lab>`
**Computation:** `q_tally.py` → `q_tally_out.json` (+ console dump `q_tally_console.txt`).
Every number below comes from that script joining `q_judgments/*.json` and
`q_rubric/*.json` against `QKEY.json` / `QPAIRKEY.json`. Re-run `python q_tally.py`
to reproduce.

**Unit of analysis:** the pairwise trial (77 judged of 144 planned) and the
rubric item-mean (72 items, 144 score rows).

---

## 0. Contamination check — clean, but read the caveat

**442 free-text strings were scanned** (`why`, `what_the_loser_did_better`,
`strongest_line`, `weakest_line`) against 29 patterns for AI / model /
generation / authorship talk.

**9 regex hits. 0 genuine contamination.** Every hit is a false positive on a
polysemous word. All nine, in full:

| #   | source      | field                     | matched  | what it actually was                                                            |
| --- | ----------- | ------------------------- | -------- | ------------------------------------------------------------------------------- |
| 1   | QP0/QT-3956 | why                       | "prompt" | "closes with an engagement **prompt**" — a call-to-action                       |
| 2   | QP0/QT-6927 | why                       | "prompt" | "the certificate **prompt**" — certbot's CLI question                           |
| 3   | QP0/QT-8728 | why                       | "prompt" | "mixes **prompt** conventions inside its own code blocks" — `$` vs `>`          |
| 4   | QP0/QT-8728 | what_the_loser_did_better | "prompt" | "Your shell **prompt** will change" — quoted from the passage                   |
| 5   | QP0/QT-8189 | why                       | "prompt" | "ends on a follow **prompt**" — a social CTA                                    |
| 6   | QP2/QT-8232 | what_the_loser_did_better | "model"  | "a buyer scans the operating **model** in five seconds"                         |
| 7   | QP6/QT-6549 | why                       | "prompt" | "the concrete benefit (no password **prompt**)"                                 |
| 8   | QR0/QX-3404 | weakest_line              | "robots" | quoted corpus text: "medical devices, and **robots**: the 'internet of things'" |
| 9   | QR2/QX-6627 | weakest_line              | "prompt" | quoted corpus text: "Your **prompt** should now carry a `(.venv)` prefix"       |

No judge referred to AI, models, generation, humanization, or authorship as a
reason for any decision. **The pairwise measurement is not compromised by
authorship reasoning.**

**But one thing did leak, and it is not authorship — it is _identity_.** In 16 of
77 trials the judge ran `diff`/`cmp` on the two files and reported the result in
the `why` field. Twelve of those found the two passages **byte-identical**. That
is not contamination of the construct being measured; it is the judges correctly
detecting that the experiment handed them the same text twice. It governs the
whole of §2 below and is the single most consequential fact in this report.

---

## 1. THE HEADLINE: raw-ai vs gate-clean

**Editors preferred the fully processed passage 22 times out of 22.**

|                          | value                           |
| ------------------------ | ------------------------------- |
| gate-clean wins          | **22 / 22**                     |
| win rate                 | **100.0%**                      |
| 95% CI (Wilson)          | **85.1% – 100.0%**              |
| exact binomial p vs 0.50 | **4.77 × 10⁻⁷**                 |
| planned n                | 36 (61% of the cell was judged) |

Not one trial went the other way, in any register, at any length:

- **by register** — email 4/4, essay 2/2, howto 4/4, marketing 3/3, review 5/5, social 4/4
- **by length** — short 8/8, medium 5/5, long 9/9

**Margin distribution** (all 22 in gate-clean's favor):

| margin    | n   | share |
| --------- | --- | ----- |
| decisive  | 4   | 18.2% |
| clear     | 18  | 81.8% |
| slight    | 0   | 0.0%  |
| coin-flip | 0   | 0.0%  |

This is the cleanest result in the study. Zero trials landed in the
slight-or-coin-flip band, which means the preference was not a whisker: judges
found a legible, statable quality gap in every single comparison. The
lower bound of the CI is 85.1% — even the pessimistic reading of this data says
the processed passage wins roughly six times in seven.

**What n would resolve it:** nothing needs resolving on the _direction_. At the
observed rate, n = 4 already excludes 0.50; we have 22. The open question is the
_magnitude of the ceiling_: with 22/22 the CI floor sits at 85.1%, and pushing
that floor above 90% requires roughly n = 36 (the full planned cell) at a
sustained 100% rate. Judging the 14 unjudged trials in this cell is the single
highest-value remaining measurement in the lab.

---

## 2. Stage attribution: which half of the pipeline earns its keep

### 2a. The rewrite pass alone

**raw-ai vs humanized: humanized 16 / 16 = 100.0%**, CI **80.6% – 100.0%**,
p = 3.05 × 10⁻⁵ (planned n = 36).
Margins: 1 decisive, 14 clear, 1 slight, 0 coin-flip.
By register 2/2, 3/3, 4/4, 3/3, 2/2, 2/2; by length 4/4, 5/5, 7/7.

### 2b. The mechanical checker stage on top

**humanized vs gate-clean: gate-clean 12 / 21 = 57.1%**, CI **36.5% – 75.5%**,
p = **0.664**. Margins: 13 coin-flip, 5 slight, 3 clear.

That is chance, and there is a mechanical reason for it.

### 2c. The reason: the checker stage usually changes nothing at all

Comparing SHA-256 hashes from `QKEY.json` across the 18 register × length cells:

| stage                  | cells changed | cells byte-identical |
| ---------------------- | ------------- | -------------------- |
| raw-ai → humanized     | **18 / 18**   | 0                    |
| humanized → gate-clean | **7 / 18**    | **11 / 18**          |
| raw-ai → gate-clean    | 18 / 18       | 0                    |

**In 11 of 18 cells the mechanical checker emitted its input unchanged, byte for
byte.** Where it did change something, the edit is microscopic: byte deltas of
+11, −14, −1, +2, −26, −3, −1 — in five of the seven cases a single clause or a
single closing sentence.

This poisons the naive 57.1% figure. Of the 21 judged humanized-vs-gate trials,
**12 compared literally the same file to itself**, and the judges caught every
one:

> "These two files are byte-identical; cmp reports no differences… There is no
> textual basis to prefer either; I picked item_a as instructed, since ties are
> not allowed." — QT-3417 (essay/short)

> "Honest report: these two files are byte-identical — 5,413 bytes each, and diff
> returns nothing… Nothing separates them." — QT-3043 (howto/long)

All 12 were logged as `coin-flip`. Split the contrast accordingly:

| subset                                 | n   | gate-clean wins | rate      | 95% CI        | p            |
| -------------------------------------- | --- | --------------- | --------- | ------------- | ------------ |
| **cells the checker actually changed** | 9   | 7               | **77.8%** | 45.3% – 93.7% | 0.180        |
| **cells it left byte-identical**       | 12  | 5               | 41.7%     | —             | forced noise |

**Verdict on stage attribution — stated plainly, as asked:**

The **rewrite pass carries essentially all of the benefit**. It moves 18/18 cells
and wins 16/16 head-to-head trials. The **mechanical checker stage does not earn
its keep as currently configured**: it declines to act in 61% of cells, and where
it does act the resulting preference (7/9, CI 45.3–93.7%) cannot be
distinguished from chance at this n. It is not established to be _harmful_ — the
point estimate on its changed cells is positive on both the pairwise (77.8%) and
the rubric (+0.93 total, CI −0.67 to +2.53) — but it is not established to do
anything.

**What n would resolve it:** at the observed pooled rate of 57.1%, excluding 0.50
needs **n ≈ 185–190** trials, five times the planned cell. That is the wrong
experiment. The right one is cheap: restrict to the **7 cells where the checker
changes the text**, judge all 14 trials there (9 done), and if the 77.8% rate
holds, **n ≈ 11** on changed cells is enough to clear 0.50. The correct fix to
the design is to stop spending trials on identical files.

---

## 3. The quality-vs-humanness dissociation

**This is the most interesting result available in this lab, and it needs to be
stated before the caveats.**

**gate-clean vs human-control: gate-clean 18 / 18 = 100.0%**, CI **82.4% –
100.0%**, p = 7.63 × 10⁻⁶.
Margins: **10 decisive**, 7 clear, 1 slight, 0 coin-flip — the most lopsided
margin profile of any contrast in the study.
By register 3/3, 3/3, 1/1, 3/3, 4/4, 4/4; by length 8/8, 6/6, 4/4.

The rubric agrees, and by a wide margin: gate-clean scores **87.1 / 100**
(CI 83.3–91.0) against human-control's **64.6** (CI 58.3–70.9), a paired gap of
**+22.56** points (CI +14.85 to +30.26), better in **17 of 18 cells**.
"Would keep reading" runs **97.4%** for gate-clean against **42.9%** for the
human prose.

**Now set that beside the prior sweep in this same corpus**
(the detection sweep summarized in [README.md](README.md)): judges called the
human-control arm human **143 times out of 143** — a 0.0% false-positive rate,
95% CI 0.0–2.6%, specificity 100.0%, mean confidence 4.95/5. The same
human passages that lose 18/18 on quality were identified as human **every
single time**. Machine-arm detection over the same instrument ran 97.8–100%.

**The dissociation:** "reads as human" and "is good writing" are behaving as
**separable, in fact anti-correlated, properties** in this corpus. The arm that
is 100% recognizable as human is the arm that loses 100% of quality trials. The
arm that is 97.8% recognizable as machine wins 100% of them. A detector saturated
at both rails and a quality panel saturated at both rails are pointing in
_opposite_ directions on the same 18 passages.

If that holds up, it dissolves the premise the pipeline is built on. The pipeline
optimizes for not-being-detected. This measurement says not-being-detected and
being-good are different axes, and the axis the pipeline targets is not the one
that makes prose better. The rewrite pass makes prose measurably better
(§2a) — it just doesn't make it pass as human (prior sweep: 98.6% still caught).

**The caveat that must travel with this claim, every time:** the human-control
arm is **found text, not a matched draft**. Per `QKEY.json` sources, it is
pre-2021 Wikipedia _Signpost_ columns, an NSF program announcement, the
Kubernetes and cloud.gov home pages, an adidas case study, the SQLite
"appropriate uses" page, the ripgrep README, and the Portal 2 critical-reception
section. It is matched to the machine arms on **register and length only** —
**not on subject**. The batch instruction told judges "Both passages address the
same subject at the same size," and for this one contrast **that instruction is
false**: the machine essay is about a neighborhood hardware store, the human
essay is about a beginner's experience editing Wikipedia. The three machine arms
_are_ genuinely subject-matched to each other (verified: identical opening
sentences across raw-ai/humanized/gate-clean per cell), so §1 and §2 are clean.
§3 is not a like-for-like contest. It compares purpose-built prose against
excerpted prose doing a different job, some of it lifted out of the document that
gave it context. Judges noticed exactly that, unprompted:

> "That anecdote has more genuine discovery in it than anything in the benches
> piece; **it is just buried in a section it does not belong to**." — QT-5875

The honest statement is therefore: **on this corpus, an editor model prefers
gate-clean prose to real human prose 18/18 times and scores it 22 points higher,
while a detector identifies that same human prose as human 143/143 times.** The
dissociation is real and large. Whether it survives a subject-matched human
control is untested, and testing it is the obvious next experiment.

---

## 4. Rubric means by arm

Each dimension is scored 0–25; total is 0–100. Cell values are **item-level mean
[95% CI]** over 18 items per arm.

| arm           | n items | specificity       | economy           | clarity           | engagement        | **total**             | would keep reading |
| ------------- | ------- | ----------------- | ----------------- | ----------------- | ----------------- | --------------------- | ------------------ |
| raw-ai        | 18      | 19.7 [17.6, 21.8] | 17.2 [15.7, 18.7] | 22.8 [22.3, 23.4] | 16.9 [15.1, 18.8] | **76.6 [71.1, 82.2]** | 27/37 = 73.0%      |
| humanized     | 18      | 21.3 [19.7, 22.9] | 22.0 [21.0, 23.0] | 23.6 [23.3, 24.0] | 19.8 [18.1, 21.5] | **86.7 [82.7, 90.7]** | 30/33 = 90.9%      |
| gate-clean    | 18      | 21.4 [19.8, 23.0] | 22.0 [21.0, 22.9] | 23.6 [23.2, 23.9] | 20.2 [18.6, 21.8] | **87.1 [83.3, 91.0]** | 38/39 = 97.4%      |
| human-control | 18      | 19.6 [18.0, 21.1] | 15.3 [13.3, 17.4] | 16.6 [14.6, 18.7] | 13.1 [10.7, 15.4] | **64.6 [58.3, 70.9]** | 15/35 = 42.9%      |

(`would keep reading` denominators are score _rows_, not items — scorer coverage
is uneven; see §7.)

**Movement through the pipeline, paired within each register × length cell**
(n = 18 cells; the paired test is the right one, since the three machine arms are
the same passage at three stages):

| dimension   | raw → humanized            | humanized → gate-clean | **raw → gate-clean**       |
| ----------- | -------------------------- | ---------------------- | -------------------------- |
| specificity | +1.63 [+0.89, +2.37]       | +0.11 [−0.27, +0.49]   | **+1.74 [+1.07, +2.41]**   |
| **economy** | **+4.81 [+3.86, +5.77]**   | −0.04 [−0.46, +0.39]   | **+4.78 [+3.69, +5.86]**   |
| clarity     | +0.77 [+0.39, +1.15]       | −0.06 [−0.26, +0.15]   | **+0.71 [+0.33, +1.09]**   |
| engagement  | +2.86 [+1.90, +3.83]       | +0.42 [+0.01, +0.82]   | **+3.28 [+2.18, +4.38]**   |
| **total**   | **+10.07 [+7.51, +12.64]** | +0.44 [−0.57, +1.44]   | **+10.51 [+7.60, +13.42]** |

Cells improved / tied / worsened, raw → gate-clean: specificity 15/2/1, economy
**18/0/0**, clarity 13/2/3, engagement 17/1/0, total **18/0/0**.

**Which dimension moves most: economy.** +4.78 points, 46% of the total gain,
improved in 18 of 18 cells, z = +5.29. The pipeline is, measurably, a
padding-removal machine. Engagement is second (+3.28, 17/18 cells).

**Which dimension does not move: clarity.** +0.71 points — and it was already at
**22.8 / 25 in the raw draft**, the highest raw-ai score of any dimension. There
is 2.2 points of headroom and the pipeline takes a third of it. Raw model output
is _already clear_; it is verbose, unspecific and dull. That is a precise
statement of what this pipeline is for and what it is not for.

Note the shape of the human-control column: it scores **within noise of raw-ai on
specificity** (19.6 vs 19.7) and loses badly on economy, clarity and engagement.
The one thing found human prose is not beaten on is concrete detail — which is
exactly what the judges say in §5b.

---

## 5. What editors said the processed prose does better — and what it destroys

### 5a. What gate-clean does better (from `why`, raw-ai vs gate-clean)

Three named mechanisms recur across all 22 trials.

**It deletes the throat-clearing.**

> "QX-2343 opens with 43 words of throat-clearing — 'Now that the quarter has
> officially closed, I wanted to send around a consolidated update covering what
> the Platform team shipped in Q3…' — where QX-6112 opens with 20: 'The quarter
> closed last week. Below is what we shipped, what broke, and what we're doing
> between now and December.'" — QT-2303 (email/long)

**It replaces a category with an image, and a maxim with a moment.**

> "QX-6832 reports; QX-9172 narrates that it is reporting… 'A customer said he'd
> assumed we were somebody's side project, because who charges $29 for something
> that does this. That stung enough to act on.' QX-9172 converts it to a maxim:
> 'That was a wake-up call. Pricing isn't just a number, it's a signal about who
> you are.'" — QT-8189 (social/medium)

**It marks the limits of its own evidence.**

> "More importantly, QX-6112 adds a sentence QX-2343 does not have: after the 31
> percent drop in on-call pages, 'The other half we cannot account for cleanly,
> so treat that number as directional.' QX-2343 reports the same figure and stops
> at the half it can explain, which quietly leaves the reader with a stronger
> impression than the data supports." — QT-2303 (email/long)

> "8734 'On a 787 the engine drone stops existing'; 7145 'On a Boeing 787 the
> engine drone essentially disappears' (hedge)." — QT-1418 (review/long)

### 5b. What the processed prose destroys — the cost side of the ledger

`what_the_loser_did_better` was populated on all 22 raw-vs-gate trials. It is the
most useful field in the study because it names what the pipeline **removes that
was worth keeping**. Three costs, and they are consistent enough to be design
notes.

**Cost 1 — it dissolves scannable structure into prose.** This is the single most
frequent complaint: **12 of 22** trials name a lost bullet, list, header, label,
enumeration, or scan/skim affordance. The pipeline's economy pass treats bulleted
lists, bolded labels and enumerations as padding and flattens them, which is
wrong for documents that get _skimmed_ rather than read.

> "QX-2343 puts the four quarterly metrics in bullets, one per line, which is
> genuinely easier to scan and to quote than QX-6112's single running
> paragraph — and for a numbers section in an all-hands email, **that formatting
> choice is defensible on its own terms**." — QT-2303 (email/long)

> "1235's How It Works is a bolded four-bullet list (Receive / Put away / Pick /
> Count) that a buyer can skim in six seconds; 1768 dissolves the same four steps
> into one paragraph and **loses the scannable spine that a landing page actually
> needs**." — QT-1324 (marketing/medium)

> "7145's bulleted Specifications at a glance block is the right call for a buying
> review: driver, weight, battery, codecs, connectivity, all scannable without
> reading a sentence. 8734 flattens the same data into a prose line… **that is
> worse to skim**." — QT-4298 (review/long)

> "5651's prerequisites work better as a literal pre-flight checklist because they
> are enumerated First/Second/Third; 6403 runs the same three items together as
> consecutive fragments that are **harder to tick off one by one**." — QT-6354 (howto/long)

**Cost 2 — it drops signposting the reader was using.** Labels, section headers
that say what is inside, and explicit connectives all read as filler to the
pipeline and as navigation to the reader.

> "QX-2599's section headers are far better scan targets for an evaluating buyer:
> 'Enterprise-Grade Security and Compliance' and 'Pricing That Scales With You'
> say what is inside, where 3229's oblique 'A different shape' and 'Where your
> team already is' would make a reader hunting for the integrations section read
> the body to find it." — QT-0634 (marketing/long)

> "QX-0153 uses thread conventions well: the opening emoji signals a multi-post
> thread, and the explicit 'Context:' label lets a scroller know instantly that
> post 2 is setup and can be skipped. 6620 gives no such signposting." — QT-9230 (social/short)

> "3229's clipped 'Teams care about writing things down. The tools make it harder
> than it should be' **asks the reader to supply the but**." — QT-1075 (marketing/long)

**Cost 3 — compression drops load-bearing nouns.** 10 of 22 trials name a
referent, spec, audience or system the compressed version left the reader to
infer. In cutting words the pipeline
sometimes cuts the specific referent, leaving the reader to infer a system name,
a spec, or an audience.

> "QX-7066 names the system: 'I've already updated the PagerDuty schedule.'
> QX-2506 says only 'The schedule is already updated', **leaving the reader to
> infer where to look**." — QT-7500 (email/short)

> "QX-7145's spec block… **names the diaphragm material ('40 mm dome, liquid
> crystal polymer diaphragm') that 8734 omits entirely**." — QT-1418 (review/long)

> "QX-3428 is more explicit about who the product is for, listing 'travelers,
> office workers, and anyone who wants a reliable single-serve brewer…' QX-3647
> leaves the office-worker case implied." — QT-9368 (review/short)

> "QX-5410 renders the click path better: 'Settings → SSH and GPG keys' with an
> arrow reads as a UI breadcrumb, where 7586's 'Settings, then SSH and GPG keys'
> is momentarily ambiguous about whether that is one menu item or two." — QT-5816 (howto/short)

**The pattern:** every one of these costs is a **skim-affordance**. The pipeline
optimizes the experience of reading a passage straight through, and it pays for
that by degrading the experience of _navigating_ one. Editors still preferred the
processed version 22/22 — the gains outweigh the costs on this rubric — but the
costs concentrate in exactly the registers where nobody reads straight through:
marketing pages, spec-heavy reviews, procedural how-tos, and all-hands emails
with a numbers section. **A pipeline that exempted lists, headers, enumerations
and UI paths from the economy pass would very likely win by more.** That is a
concrete, testable design change and it falls directly out of this field.

### 5c. What human prose did better (gate-clean vs human-control)

Even losing 18/18, human prose was credited with one thing the machine arm never
supplied: **unfakeable particularity, and the willingness to cost the author
something.**

> "QX-8750 has circumstantial specificity **no drafted essay would invent**: a
> teacher asking for material on interpretative journalism only because Wikipedia
> had no page on it, and 'over 1.2 million views at the time of counting in
> August 2018.'" — QT-0223

> "QX-6003 does something rare and trust-building: it is a tool's own
> documentation arguing when _not_ to use it, and it concedes the field to a named
> rival without qualification — 'The best tool for this job is good old grep.'
> **Nothing in 3647 costs its author anything comparable.**" — QT-6069

> "4382's opening has a vulnerability 3829 never risks — 'I'm very nervous about
> posting here, as I know everyone is much more used to the space than I am.'" — QT-5259

> "QX-2149 has the better raw material by a distance, and it does one thing
> marketing prose almost never does: **it includes a failure**… The VM-requisition
> quote is also unfakeable in a way that 'onboarding time drops by about a third'
> is not." — QT-6592

> "QX-7734 sources every judgment to a named critic and outlet… and it deliberately
> **preserves dissent**… giving a spread of opinion that a single-reviewer piece
> like QX-8734 structurally cannot offer." — QT-1905

This is the same finding as §4's rubric column read from the other side: human
prose ties the machine on **specificity** (19.6 vs 21.4) and loses everywhere
else. What it has is _real_ specificity — verifiable, sourced, self-costing —
against the machine's _manufactured_ specificity. The rubric cannot tell those
apart. No instrument in this lab can.

---

## 6. Position bias and inter-judge agreement

**Position bias.** Across all 77 trials, judges chose item **A 46 times = 59.7%**
(CI 48.6% – 70.0%, exact p vs 0.50 = **0.110**). Not significant overall, but the
point estimate leans A and the per-contrast breakdown localizes it:

| contrast                    | n   | chose A | rate      |
| --------------------------- | --- | ------- | --------- |
| raw-ai vs gate-clean        | 22  | 12      | 54.5%     |
| raw-ai vs humanized         | 16  | 9       | 56.3%     |
| **humanized vs gate-clean** | 21  | **17**  | **81.0%** |
| gate-clean vs human-control | 18  | 8       | 44.4%     |

The 81.0% is not a bias in the ordinary sense — it is the tie-breaking rule
becoming visible. Twelve of those 21 trials compared identical files and the
judges said outright that they "picked item_a as instructed, since ties are not
allowed." **Position preference appears exactly where and only where the content
signal is zero**, which is the expected and reassuring pattern. Every contrast
with a real signal sits within 6 points of 50%.

**Inter-judge agreement.** 18 pairs were judged in both orientations by
different batches (QP2 and QP6). They agreed on the winning _item_ **15 / 18 =
83.3%** (CI 60.8% – 94.2%), against a 50% chance baseline — κ vs chance = 0.67.

**All three disagreements are in humanized vs gate-clean** (howto/long,
social/short, email/short) — the only contrast where the texts are near-identical.
Agreement on raw-vs-gate and gate-vs-human orientation pairs was perfect within
this double-judged set. 41 further pairs were judged in one orientation only,
because the batch dispatch was incomplete.

**Rubric scorer reliability.** 56 of 72 items received ≥2 independent scorers.
Pearson r on totals = **0.939**; mean absolute difference **3.82 points out of
100**; worst case 17 points. The rubric instrument is reliable.

---

## 7. Data integrity — what is actually here

Reported honestly, because the coverage shortfall is large.

**Pairwise: 77 of 144 planned trials judged (53.5%).**

| contrast                    | judged | planned |
| --------------------------- | ------ | ------- |
| raw-ai vs gate-clean        | 22     | 36      |
| raw-ai vs humanized         | 16     | 36      |
| humanized vs gate-clean     | 21     | 36      |
| gate-clean vs human-control | 18     | 36      |

Of 8 planned batch files, 5 carry judgments (QP0, QP2, QP6, QP7 complete at 18
each; QP5 partial at 5). **QP4 exists but is empty** (`"status": "in-progress"`,
`"trials": []`). QP1 and QP3 were never written. **0 duplicate trial ids, 0
conflicting judgments, 0 orphan trial ids** — everything present is internally
consistent and joins cleanly to `QPAIRKEY.json`.

**Rubric: 72 of 72 items scored, 144 score rows — but misallocated.** The design
called for 6 batches × 24 items = 2 independent scorers per item. In fact
**QR0 and QR1 both scored batch RB-1**, and **RB-6 was never scored as a batch**.
Net effect on scorer coverage: 16 items got 1 scorer, 40 got 2, 16 got 3. Every
item is covered, so no arm is missing data, and batch membership is a seeded
random draw so the misallocation is unbiased across arms in expectation — but the
per-item precision is uneven.
Auxiliary working files (`QR0.jsonl`, `QR4.jsonl`, `chunk.json`, `scores.jsonl`)
were checked and are strict duplicates of rows already in the canonical `QR*.json`
batch files; the script verifies this and excludes them rather than
double-counting.

---

## 8. Limitations — read these as binding on every number above

1. **One corpus.** 18 register × length cells, six registers, one authoring pass.
   Nothing here generalizes past this corpus without a replication on a second one.

2. **Same model family on both sides of the glass.** The prose was written by an
   agent from one model family and scored by agents from the same family. A model
   preferring the register its own family produces is not evidence that the prose
   is good; it is at minimum a shared-prior confound, and it plausibly _inflates
   every machine-arm result in this report_ — including, and especially, the
   18/18 win over human prose in §3. This is the most serious threat to the
   headline finding and it cannot be ruled out with the data in this lab.

3. **"An editor model prefers it" is not "a human reader prefers it."** Every
   result here is a statement about a judge's stated preference in a forced
   two-alternative choice, with no ties permitted, in a task framed as evaluating
   writing quality. No human read any of these passages. No reader behavior
   — time on page, completion, recall, action taken — was measured. The
   `would_keep_reading` field is a model's self-report about a hypothetical, not a
   behavior.

4. **Small n per cell, and thinner than planned.** 16–22 trials per contrast
   against 36 planned; the register × length breakdowns run 1–5 trials per bucket
   and are indicative only. The §2c changed-cells analysis rests on 9 trials.

5. **The human-control arm is not subject-matched** (§3), and the batch
   instruction incorrectly told judges it was. It is also _found_ text serving
   its original purpose, excerpted — some of it, as judges noticed, from a
   surrounding document that carried its context.

6. **The no-ties rule manufactures signal from nothing.** Twelve trials compared
   byte-identical files and still produced a "winner." Those picks are in the
   57.1% figure in §2b and are pure noise; the report separates them, but any
   downstream reuse of the raw contrast number will not.

7. **Forced-choice inflates apparent decisiveness.** A 100% win rate in a
   two-alternative forced choice with a shared-family judge is not the same claim
   as "this prose is 100% better," and the CI floors (85.1%, 80.6%, 82.4%) are
   the honest read.

8. **The rubric cannot see provenance of fact.** §5c shows judges crediting human
   prose for verifiable, sourced, self-costing specificity — and then scoring both
   arms on a `specificity` dimension that treats invented concrete detail and real
   concrete detail identically. Manufactured specificity scores the same as earned
   specificity. Every specificity number in §4 should be read with that in mind.

---

## 9. What to do next, in priority order

1. **Finish the raw-ai vs gate-clean cell** (14 unjudged trials). It is the
   headline and it is 61% measured.
2. **Re-scope the checker-stage experiment to the 7 cells where the checker
   changes the text.** Judging identical files burns trials and manufactures
   coin-flips. At the observed 77.8%, n ≈ 11 on changed cells settles it.
3. **Build a subject-matched human control** — a human writing to the same brief
   as the machine arms — and re-run §3. Until that exists, the dissociation is
   the most interesting result in the lab and the least defensible.
4. **Exempt lists, headers, enumerations and UI paths from the economy pass**, and
   re-run raw-vs-gate. §5b says this is where the pipeline pays its costs, and the
   costs concentrate in marketing, review, howto and email.
5. **Score one arm with a judge from a different model family** to size the
   shared-prior confound in limitation 2.
