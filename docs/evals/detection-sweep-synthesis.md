<!-- The analyst agent's narrative synthesis, vendored verbatim apart from three
     mechanical edits: local paths scrubbed, the tool renamed, and spelling
     normalized to American English. No number, table or judgment was altered.
     This is the document the README's corrections were drawn from, and it is the
     authority where it and any summary disagree. -->

# Humanist paragraphing sweep: synthesis

**Corpus:** 72 source passages x 4 paragraphing treatments = 288 blinded items.
**Judgments:** 24 batch files, 576 calls, two nominally independent passes.
**Computation:** a `tally.py` script joining the judgment files to the blinding key.
Every number in this document comes from that script. Its generated tables are
vendored here as [detection-sweep.md](detection-sweep.md); the harness itself, the
blinding key and the raw judgment files were run outside this repository to keep
generated transcripts out of version control, so the script's own path references
above are to that lab directory rather than to anything in this tree. The design is
described in [README.md](README.md) in enough detail to rebuild.

---

## Read this before the headline

**The control arm produced a false-positive rate of 0.0% -- 0 `ai` calls out of 143
calls on genuine pre-2021 human prose (95% CI 0.0-2.6%).** Mean confidence on those
calls was 4.95 out of 5; all 143 were confidence 4 or 5. Specificity is 100.0%.

That is the yardstick, and it cuts in an unexpected direction. The brief anticipated a
_high_ control rate, in which case a low detection rate on machine prose would mean a
blunt instrument. The opposite happened. The judge is not blunt -- it is **saturated**.
With false positives at 0% and machine-arm detection at 98.8% (428/433), the
instrument has no dynamic range left. Every remaining measurement in this sweep is
being taken through a device pinned to both rails.

Three consequences, all of which govern how the rest of this document should be read:

1. **The pipeline's measured effect is not measurable.** raw-ai 100.0% -> gate-clean
   97.8% is a -2.2 pp difference against a design that could not resolve anything
   smaller than about 3.6 pp at 80% power. The correct statement is "no effect
   detected", not "an effect of -2.2 pp".
2. **The paragraphing hypothesis could not have been confirmed in the raw-ai arm at
   all.** Detection there is exactly 100.0% for all four treatments. A ceiling cannot
   move up.
3. **A 0% false-positive rate means the sweep produced zero false tells.** The
   deliverable "features the checker must never encode, mined from misclassified human
   prose" has no direct empirical basis in this run. Section 5 gives the nearest
   honest substitute and says plainly that it is a substitute.

The judgments themselves are not noise. Cross-pass raw agreement is 98.0% (kappa 0.946,
PABAK 0.960) over the 198 items both passes saw; the four batches accidentally
dispatched twice agreed 100.0% (96 pairs). The instrument is reliable. It is reliable
and uninformative at the same time, which is a specific failure mode, not a good result.

---

## Headline

**On this corpus, against this judge, the humanist pipeline does not work, and
paragraph shape does not matter.**

- Raw model output was caught 153/153 times.
- Humanizer-rewritten output was caught 141/143 times (98.6%).
- Gate-clean output -- through the humanizer _and_ the mechanical gate -- was caught
  134/137 times (97.8%).
- The full pipeline bought a -2.2 pp change in detection, inside the noise floor of the
  design, against a control arm at 0.0%.
- Removing every paragraph break (`chunk`) did **not** raise detection. Within the
  machine arms it went 97.2% (as-authored) -> 99.1% (chunk), a +1.9 pp move in the
  hypothesized direction that is smaller than the minimum detectable difference and is
  plausibly explained entirely by a reflow artifact (section 4).

Five items out of 433 machine-arm calls escaped. All five are quoted in full in
`RESULTS.md` section 7.2b. They cluster hard: 3 of 5 are `social` register, 2 are
`howto`, none is `essay`, `marketing`, `email` or `review`; **all 5 are gate-clean (3) or
humanized (2), and none is raw-ai.** That is the only observed evidence that the pipeline ever
does anything, and it is 5 events.

---

## 1. Detection by arm

| arm           | n calls | ai calls | detection  | 95% CI     | conf-weighted | mean conf |
| ------------- | ------- | -------- | ---------- | ---------- | ------------- | --------- |
| raw-ai        | 153     | 153      | **100.0%** | 97.6-100.0 | 100.0%        | 4.35      |
| humanized     | 143     | 141      | **98.6%**  | 95.0-99.6  | 98.8%         | 3.48      |
| gate-clean    | 137     | 134      | **97.8%**  | 93.8-99.3  | 98.4%         | 3.56      |
| human-control | 143     | 0        | **0.0%**   | 0.0-2.6    | 0.0%          | 4.95      |

Mean confidence is the one place the pipeline shows up cleanly: 4.35 on raw-ai versus
3.48 / 3.56 on the processed arms. The pipeline does not change the verdict; it makes
the judge less sure while it delivers the same verdict. That is a real, monotone,
directionally-correct signal and it is the strongest thing that can be said for the
pipeline from this data.

---

## 2. Detection by paragraphing treatment -- the primary hypothesis

### Manipulation check

| treatment   | items | mean paragraphs | median | min | max | % single block |
| ----------- | ----- | --------------- | ------ | --- | --- | -------------- |
| as-authored | 72    | 15.00           | 12     | 1   | 57  | 1.4%           |
| chunk       | 72    | 1.00            | 1      | 1   | 1   | 100.0%         |
| punchy      | 72    | 29.51           | 23     | 4   | 115 | 0.0%           |
| irregular   | 72    | 13.50           | 11     | 1   | 51  | 1.4%           |

The manipulation is real. I re-verified the word-identity assertion independently of
`make_variants.py`: 288 of 288 item files are byte-identical to their source passage
after whitespace normalization, 0 differing, 0 missing. **The assertion in
`make_variants.py` holds.** Every treatment of a passage is the same tokens in the same
order, so a difference between treatments is attributable to paragraph shape and
nothing else -- no wording, length, topic or register confound is possible by
construction. That is a genuinely clean comparison and it is the best feature of this
design. One caveat surfaced by the judges themselves is at section 4.

### Marginal rates, all arms pooled -- and why they must not be quoted

| treatment   | n calls | detection | 95% CI    |
| ----------- | ------- | --------- | --------- |
| as-authored | 138     | 74.6%     | 66.8-81.2 |
| chunk       | 153     | **71.9%** | 64.3-78.4 |
| punchy      | 141     | 75.2%     | 67.4-81.6 |
| irregular   | 144     | 75.7%     | 68.1-82.0 |

Read naively this says `chunk` is detected _least_ often -- the opposite of the
hypothesis. It says nothing of the kind. The control arm is at a 0.0% floor and the
machine arms at a 97-100% ceiling, so a treatment's pooled rate is close to a
restatement of how many control calls landed in it, and the lost batches made those
shares unequal:

| treatment   | n calls | raw-ai | humanized | gate-clean | human-control | control share |
| ----------- | ------- | ------ | --------- | ---------- | ------------- | ------------- |
| as-authored | 138     | 36     | 37        | 33         | 32            | 23.2%         |
| chunk       | 153     | 36     | 38        | 37         | 42            | **27.5%**     |
| punchy      | 141     | 40     | 33        | 33         | 35            | 24.8%         |
| irregular   | 144     | 41     | 35        | 34         | 34            | 23.6%         |

`chunk` carries the largest control share and therefore the lowest pooled rate. **This
is a textbook composition artifact and it points the wrong way**, which is exactly why
the brief's instruction to check whether an effect survives within-stratum matters.

### The interpretable version

| treatment   | machine arms only | n   | human-control only | n   |
| ----------- | ----------------- | --- | ------------------ | --- |
| as-authored | 97.2%             | 106 | 0.0%               | 32  |
| chunk       | **99.1%**         | 111 | 0.0%               | 42  |
| punchy      | 100.0%            | 106 | 0.0%               | 35  |
| irregular   | 99.1%             | 110 | 0.0%               | 34  |

### Full arm x treatment cross-tab (detection %, n in parentheses)

| arm           | as-authored | chunk       | punchy      | irregular   | arm total    |
| ------------- | ----------- | ----------- | ----------- | ----------- | ------------ |
| raw-ai        | 100.0% (36) | 100.0% (36) | 100.0% (40) | 100.0% (41) | 100.0% (153) |
| humanized     | 97.3% (37)  | 97.4% (38)  | 100.0% (33) | 100.0% (35) | 98.6% (143)  |
| gate-clean    | 93.9% (33)  | 100.0% (37) | 100.0% (33) | 97.1% (34)  | 97.8% (137)  |
| human-control | 0.0% (32)   | 0.0% (42)   | 0.0% (35)   | 0.0% (34)   | 0.0% (143)   |
| all arms      | 74.6% (138) | 71.9% (153) | 75.2% (141) | 75.7% (144) | 74.3% (576)  |

### Effect size and verdict

| contrast                                         | chunk       | comparison  | delta       | OR (Haldane) |
| ------------------------------------------------ | ----------- | ----------- | ----------- | ------------ |
| chunk vs (as-authored + irregular), all arms     | 71.9% (153) | 75.2% (282) | **-3.3 pp** | 0.84         |
| chunk vs (as-authored + irregular), machine arms | 99.1% (111) | 98.1% (216) | **+1.0 pp** | 1.56         |
| within raw-ai                                    | 100.0% (36) | 100.0% (77) | 0.0 pp      | zero cell    |
| within humanized                                 | 97.4% (38)  | 98.6% (72)  | **-1.2 pp** | 0.52         |
| within gate-clean                                | 100.0% (37) | 95.5% (67)  | **+4.5 pp** | zero cell    |
| within human-control                             | 0.0% (42)   | 0.0% (66)   | 0.0 pp      | zero cell    |

**Verdict: the hypothesis is not supported.** The aggregate delta is negative and is a
composition artifact. The within-machine-arm delta is +1.0 pp, positive but below the
~3.6 pp this design could resolve at 80% power. The sign is not consistent across arms:
one arm is positive (+4.5, gate-clean, on 37 vs 67 calls), one is negative (-1.2,
humanized), two are flat at their rails. **An effect that appears only in aggregate is a
composition artifact; an effect that appears in one of four arms on a hundred calls is a
coin.** Neither is a finding.

What the design can honestly conclude: **no paragraph-shape effect larger than roughly
4 pp exists on machine text this judge already detects 98.8% of the time.** A real test
of the paragraphing hypothesis needs a judge that is not at the ceiling.

### Treatment x register

| treatment   | email      | essay      | howto      | marketing  | review     | social     |
| ----------- | ---------- | ---------- | ---------- | ---------- | ---------- | ---------- |
| as-authored | 71.4% (21) | 77.3% (22) | 81.5% (27) | 77.3% (22) | 75.0% (24) | 63.6% (22) |
| chunk       | 66.7% (24) | 72.4% (29) | 59.1% (22) | 72.7% (22) | 79.3% (29) | 77.8% (27) |
| punchy      | 79.2% (24) | 76.0% (25) | 75.0% (24) | 70.8% (24) | 82.6% (23) | 66.7% (21) |
| irregular   | 84.0% (25) | 77.8% (27) | 75.0% (20) | 77.3% (22) | 76.0% (25) | 64.0% (25) |

These cells run 20-29 calls each and inherit the same control-share contamination.
No cell in this table supports a claim.

---

## 3. Register, length, and their interaction with arm

| register  | n calls | detection | 95% CI    |
| --------- | ------- | --------- | --------- |
| review    | 101     | 78.2%     | 69.2-85.2 |
| essay     | 103     | 75.7%     | 66.6-83.0 |
| email     | 94      | 75.5%     | 66.0-83.1 |
| marketing | 90      | 74.4%     | 64.6-82.3 |
| howto     | 93      | 73.1%     | 63.3-81.1 |
| social    | 95      | 68.4%     | 58.5-76.9 |

| length band | n calls | detection | 95% CI    |
| ----------- | ------- | --------- | --------- |
| short       | 188     | 75.5%     | 68.9-81.1 |
| medium      | 203     | 75.4%     | 69.0-80.8 |
| long        | 185     | 71.9%     | 65.0-77.9 |

Again: pooled marginals, contaminated by control share. The conditional tables are the
real ones, and they are where the only structure in this entire sweep lives.

### Length x arm

| length band | raw-ai      | humanized   | gate-clean     | human-control |
| ----------- | ----------- | ----------- | -------------- | ------------- |
| short       | 100.0% (47) | 100.0% (45) | 98.0% (51)     | 0.0% (45)     |
| medium      | 100.0% (56) | 98.1% (53)  | 100.0% (45)    | 0.0% (49)     |
| long        | 100.0% (50) | 97.8% (45)  | **95.1% (41)** | 0.0% (49)     |

### Register x arm

| register  | raw-ai      | humanized   | gate-clean     | human-control |
| --------- | ----------- | ----------- | -------------- | ------------- |
| email     | 100.0% (25) | 100.0% (24) | 100.0% (22)    | 0.0% (23)     |
| essay     | 100.0% (26) | 100.0% (25) | 100.0% (27)    | 0.0% (25)     |
| howto     | 100.0% (26) | 95.8% (24)  | 95.0% (20)     | 0.0% (23)     |
| marketing | 100.0% (22) | 100.0% (18) | 100.0% (27)    | 0.0% (23)     |
| review    | 100.0% (31) | 100.0% (25) | 100.0% (23)    | 0.0% (22)     |
| social    | 100.0% (23) | 96.3% (27)  | **88.9% (18)** | 0.0% (27)     |

**The one suggestive pattern in the sweep:** gate-clean survives best in `social`
(88.9%, n=18) and `howto` (95.0%, n=20), and best at `long` length (95.1%, n=41). All
five escapes fall in `social` or `howto`. On 18-41 calls per cell this is a hypothesis,
not a result -- but it is the hypothesis worth spending the next sweep on, because it is
the only cell structure that survives conditioning on arm.

---

## 4. A confound the judges found for us

Judges cited 15 feature strings across 13 items describing damage the re-paragraphing
introduced: headings fused into the following sentence, code fences run together, tweet
numbers welded to the previous line, the document collapsed to a single block.
Distribution by treatment: **chunk 2, punchy 8, irregular 5, as-authored 0.**

Zero on `as-authored`. The word-identity assertion holds at the token level, but
whitespace normalization does not preserve markdown _block_ structure -- `## Heading`
becomes part of the next sentence once the blank line goes. So `as-authored` is the only
treatment whose document structure is undamaged, and the three synthetic treatments each
carry a small artificial tell the hypothesis did not intend.

The direction matters and it makes the null result stronger, not weaker. The artifact
should have inflated detection on chunk/punchy/irregular relative to as-authored.
Machine-arm detection was 97.2% for as-authored against 99.1 / 100.0 / 99.1 -- a gap of
at most 2.8 pp, in the direction the artifact predicts, small enough that the artifact
alone could account for all of it. **Read the paragraphing null as: no paragraph-shape
effect was detectable above a reflow artifact of this size.**

Fix for the next sweep: strip markdown to plain prose _before_ applying the paragraphing
treatments, so that block structure cannot differ between them.

---

## 5. Feature mining

3,522 `features` strings across 576 calls (mean 6.11 per call). Pools:

| pool            | strings | what it is                                                         |
| --------------- | ------- | ------------------------------------------------------------------ |
| true tells      | 2,632   | cited on correct `ai` calls                                        |
| **false tells** | **0**   | cited on `ai` calls against human-control -- **the pool is empty** |
| human evidence  | 859     | cited on correct `human` calls                                     |
| escapes         | 31      | cited on the 5 machine items called `human`                        |

Clustering is regex over the judges' own wording, 31 named clusters, multi-label.
**34.8% of the true-tell pool (915 strings) matched no cluster** and is sampled verbatim
in `RESULTS.md` 7.5 rather than hidden.

### 5.1 The false-tell deliverable cannot be produced from this data

There were zero false positives, so there is no measured set of "false tells the checker
must never encode". That is the honest answer and it will not be padded.

The defensible substitute is a **discrimination ratio**: a construction's share of the
2,632-string AI-evidence pool divided by its share of the 859-string human-evidence
pool. A construction cited as proof of machine authorship on machine text _and_ as proof
of human authorship on human text is not a tell; encoding it as a hard rule would
generate false positives against real writing even though this sweep never observed one.

| cluster                       | cited as AI evidence | cited as HUMAN evidence | ratio | verdict               |
| ----------------------------- | -------------------- | ----------------------- | ----- | --------------------- |
| self-answered-question        | 0                    | 2                       | 0.00  | **DANGEROUS**         |
| typography-and-punctuation    | 62                   | 33                      | 0.61  | **DANGEROUS**         |
| performed-hedging             | 137                  | 50                      | 0.89  | **DANGEROUS**         |
| chunking-artifact             | 15                   | 3                       | 1.63  | AMBIGUOUS             |
| listicle-in-prose             | 108                  | 12                      | 2.94  | AMBIGUOUS             |
| participial-significance-tail | 9                    | 1                       | 2.94  | AMBIGUOUS             |
| concessive-then-correct       | 72                   | 6                       | 3.92  | AMBIGUOUS             |
| aphoristic-closer             | 158                  | 5                       | 10.31 | SAFE                  |
| too-complete-no-friction      | 137                  | 4                       | 11.18 | SAFE                  |
| uniform-beat-rate             | 256                  | 6                       | 13.93 | SAFE                  |
| closing-formula               | 102                  | 2                       | 16.64 | SAFE                  |
| tricolon-and-triads           | 329                  | 3                       | 35.79 | SAFE                  |
| announced-thesis              | 198                  | 1                       | 64.62 | SAFE                  |
| (14 further clusters)         | --                   | 0                       | inf   | SAFE (no human cites) |

**Three findings here are worth more than the rest of the sweep:**

1. **`performed-hedging` is the third-most-cited AI tell (137 cites, 84 items) and it is
   cited on human prose almost as heavily (50 cites).** Judges called out "the hedge
   reads as inserted rather than felt" on machine text and "immediately self-qualified
   as a conservative estimate, not a hard upper bound" as _proof of humanity_ on the
   SQLite docs. Hedging is not a tell. Its _placement_ might be. Do not encode it.
2. **Dash and quote typography is cited on both sides at near parity (62 vs 33).**
   Judges cited "en dash rather than em dash" as a human signature four separate times.
   The gate ships `em/en dash` as a hard FAIL. The evidence here does not support a hard
   FAIL; it supports a house-style preference. The config already exposes
   `severity_overrides` for exactly this -- use it.
3. **`self-answered drama question` is a shipped FAIL rule with zero support.** Across
   2,632 strings of AI evidence it was cited 0 times, and it was cited twice as human
   evidence. Either the corpus never contained the construction, or judges do not weigh
   it. Worth a targeted probe before the next release.

### 5.2 What the gate already encodes vs what is new

`humanist.py` CHECKS: **41 rules.** `ai-tropes.md`: **37 bolded entries.**

| cluster                         | cites | items | status                                 |
| ------------------------------- | ----- | ----- | -------------------------------------- |
| tricolon-and-triads             | 329   | 144   | **PARTIAL**                            |
| uniform-beat-rate               | 256   | 128   | **NEW**                                |
| announced-thesis                | 198   | 106   | **PARTIAL**                            |
| negative-parallelism            | 185   | 100   | ENCODED                                |
| aphoristic-closer               | 158   | 94    | **NEW**                                |
| performed-hedging               | 137   | 84    | NEW -- _do not encode, see 5.1_        |
| too-complete-no-friction        | 137   | 67    | **NEW**                                |
| listicle-in-prose               | 108   | 71    | ENCODED                                |
| closing-formula                 | 102   | 67    | ENCODED                                |
| contraction-register-uniformity | 100   | 64    | **PARTIAL**                            |
| concessive-then-correct         | 72    | 39    | PARTIAL                                |
| ai-vocabulary                   | 71    | 33    | ENCODED                                |
| unattributed-proof              | 64    | 35    | ENCODED                                |
| typography-and-punctuation      | 62    | 38    | ENCODED -- _evidence against, see 5.1_ |
| stock-idiom-and-cliche          | 57    | 38    | PARTIAL                                |
| planted-detail-callback         | 39    | 30    | **NEW**                                |
| anaphora                        | 38    | 25    | ENCODED                                |
| balanced-clause-symmetry        | 38    | 25    | **NEW**                                |
| genre-template-completion       | 20    | 16    | **NEW**                                |
| numbers-as-texture              | 18    | 15    | **NEW**                                |
| feature-benefit-marketing       | 16    | 15    | **NEW**                                |
| chunking-artifact               | 15    | 13    | experimental artifact, not a tell      |
| fragment-paragraph-beats        | 14    | 13    | PARTIAL                                |
| internal-arithmetic-failure     | 12    | 9     | **NEW**                                |
| stock-opener                    | 11    | 11    | PARTIAL                                |
| participial-significance-tail   | 9     | 9     | ENCODED                                |
| teacherly-overexplaining        | 5     | 5     | ENCODED                                |
| stakes-inflation                | 2     | 2     | ENCODED                                |
| canonical-entity-list           | 2     | 2     | NEW                                    |
| self-answered-question          | 0     | 0     | ENCODED -- _zero support_              |
| thematic-tidiness               | 0     | 0     | no data                                |

Union coverage of the 2,632-string true-tell pool (unions, not sums, since one string
can match more than one cluster): **ENCODED clusters touch 624 strings (23.7%)**, PARTIAL
touch 753 (28.6%), NEW touch 731 (27.8%). The single
largest cited cluster in the sweep, `tricolon-and-triads` at 329 cites over 144 items,
has **no regex at all** -- `ai-tropes.md` names "Tricolon abuse" and the gate does not
implement it.

---

## 6. The deliverable: new tells, ranked, with proposed rule text

Ranked by citations on correct `ai` calls. `S` = safe by the section 5.1 ratio.

### 1. Uniform beat rate -- 256 cites, 128 items, ratio 13.93 (S) -- NEW

Every paragraph or section lands the same number of rhetorical beats; sections built to
identical shape; cadence that never varies. Cited more than any other structural
property. Verbatim: _"Both incidents narrated in identical shape -- cause, blast radius,
exact duration, then a we've-since-added remediation"_; _"Four bolded verb bullets of
machine-uniform length and grammatical shape"_.

**Proposed rule (computable, WARN, `--mode post`):** for pieces with >= 5 paragraphs,
compute the coefficient of variation of paragraph length in sentences and report it as a
band, in the same family as the existing `med`/`le5`/`gt20` bands, never as a regex. Flag
low variation as `structural-uniformity: paragraph lengths do not vary`. **The threshold
must be calibrated before shipping -- this sweep did not measure paragraph-length CV on
the control arm, so no number is proposed here.** Calibrate against
`corpus/*/human-control/` and the operator's own published writing via the existing
`--calibrate` flow.

### 2. Aphoristic closer -- 158 cites, 94 items, ratio 10.31 (S) -- NEW

An epigram terminates the paragraph or the piece. Verbatim: _"An epigram terminates
nearly every paragraph"_; _"Reading isn't a productivity metric, and treating it like one
turned a pleasure into a chore"_.

**Proposed rule (computable, WARN):** flag paragraph-final sentences that are (a) <= 12
words, (b) contain no proper noun, numeral, or first-person pronoun, and (c) use a
generalising present-tense copula. Report as
`aphoristic-close: N of M paragraphs end on a generalisation` and FAIL above 40%. This
is the highest-value new rule that a regex family can actually reach.

### 3. Completeness with no friction -- 137 cites, 67 items, ratio 11.18 (S) -- NEW

No dead ends, no digressions, no unresolved thread, the idealised path only. Verbatim:
_"Every sentence advances the argument; no digression, no aside, no dead end"_;
_"Omits every real-world wrinkle a practitioner hits: no passphrase prompt, no
~/.ssh/config, no macOS keychain flag"_; _"Perfectly closed arc in under 200 words --
spreadsheet, number, disappointment, deletion, moral"_.

**Proposed rule: MANUAL, added to the `ai-tropes.md` composition section.** No honest
regex exists. Editor-pass text: _"Name one thing that went wrong and stayed wrong. A
piece in which every problem raised is also solved reads as generated regardless of its
sentences."_ This is the highest-signal item on the list that the gate can never
mechanise, and pretending otherwise would be worse than documenting it.

### 4. Planted-detail callback -- 39 cites, 30 items, ratio inf (S) -- NEW

A distinctive detail planted early and recalled at the close; ring composition with no
loose ends. Verbatim: _"Motif planted and then recalled exactly once: 'a drawer labeled
in handwriting' in paragraph two, 'the drawer labeled in handwriting' in the final
paragraph"_.

**Proposed rule (computable, WARN):** extract noun phrases of >= 3 tokens that occur
exactly twice in the piece; flag when one occurrence is in the first 25% and the other in
the last 15% with no occurrence between. Reported as
`ring-composition: "<phrase>" planted at p1 and recalled at close`. Deliberate callbacks
are legitimate craft, so WARN and cap at one per piece.

### 5. Balanced-clause symmetry / chiasmus -- 38 cites, 25 items, ratio inf (S) -- NEW

Verbatim: _"Chiasmus as the positioning line: 'The software adapts to your team instead
of asking your team to adapt to it.'"_; _"Constructed antimetabole doing the
justification work"_.

**Proposed rule (regex, WARN):** within one sentence, detect
`\b(\w{4,})\b[^.?!\n]{2,60}\b(\w{4,})\b[^.?!\n]{0,25}\b\2\b[^.?!\n]{2,60}\b\1\b`
(two content words reappearing in reversed order). Name it
`chiasmus / antimetabole [judge in context; cap 1 per piece]`. Sits naturally beside the
existing `circular causal` rule, which already uses a backreference of this shape.

### 6. Genre-template completion -- 20 cites, 16 items, ratio inf (S) -- NEW

Every slot of the genre template filled once, in order, nothing skipped. Verbatim:
_"Fills every slot of the product-review template exactly once, in order, with nothing
left over"_; _"unskipped seven-section review template"_.

**Proposed rule: MANUAL.** Editor-pass text: _"If the piece can be mapped onto the
standard shape for its genre with no slot missing and no slot doubled, cut a slot."_

### 7. Numbers as texture -- 18 cites, 15 items, ratio inf (S) -- NEW

Concrete numbers deployed at an unnaturally even rate as authenticity props. Verbatim:
_"Numbers deployed as texture at an unnaturally even rate: 'once every four seconds',
'six blocks', 'since 1961', 'about three seconds'"_.

**Proposed rule (computable, WARN):** numeral density per 100 words, plus the CV of the
gaps between numerals. Flag when density is high _and_ gap-CV is low -- evenly sprinkled
numbers, not clustered ones. Clustered numbers are what real evidence looks like.

### 8. Feature-then-benefit positioning line -- 16 cites, 15 items, ratio inf (S) -- NEW

**Proposed rule (regex, WARN, marketing register only):** the positioning-line shape
`\b(?:instead of|rather than) [^.?!\n]{5,60}, [^.?!\n]{5,60}\b` combined with a
manufactured pull-quote frame `\b(?:said it best|put it best)\b` as FAIL. The pull-quote
frame is the clean half; the positioning line overlaps chiasmus above.

### 9. Internal arithmetic failure -- 12 cites, 9 items, ratio inf (S) -- NEW

Numbers that do not reconcile: a headline total that balances while a derived figure does
not. Verbatim: _"Top-line budget balances exactly ($61,000 + $36,000 - $94,000 = $3,000;
137/220 = 62%) but a derived figure does not: forty percent of 220 tickets discounted
$160 is about $14,000, not the stated figure"_.

**Proposed rule: a checker, not a regex.** Extract currency and percentage figures with
their operator context and verify stated sums, differences and percentages. Distinctive
because it is a tell that cannot be produced by _stylistic_ rewriting at all -- it
survives the humanizer and the gate untouched, and a writer with real numbers does not
produce it. Highest ratio of diagnostic value to implementation cost on this list.

### 10. Canonical entity list -- 2 cites, 2 items -- NEW

_"DORA-canonical metric selection -- the four a model reaches for when asked for platform
numbers"_; _"Integration-name carpet-bombing"_. Two observations. Recorded, not
recommended.

### Highest-value upgrades to rules that already exist

These are not new, but the citation counts say they are mis-weighted today.

| #   | cluster                         | cites                  | today                                                                                           | proposed                                                                                                                                                                                                                               |
| --- | ------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| U1  | tricolon-and-triads             | **329**                | named in `ai-tropes.md`, **no regex**                                                           | implement: detect `A, B, and C` coordinate triples with parallel heads; report per-1k rate; FAIL above a calibrated band. Also `announced count then exactly N` (`"Three findings"` -> exactly three). Biggest single gap in the gate. |
| U2  | announced-thesis                | **198**                | 4 partial rules (`verdict-preamble`, `throat-clearing`, `verdict frame`, `announcing the move`) | widen to the essayistic hinge: `\bI keep coming back to\b`, `\bwhat (?:this                                                                                                                                                            | that) (?:gets at\|misses)\b`, `\bthe (?:usual\|standard) conversation about\b` |
| U3  | contraction-register-uniformity | **100**                | only via uncalibrated `--mode post` marker bands                                                | promote to a first-class band: contractions per 1k words, with a hard FAIL at zero contractions in a first-person or consumer-facing register                                                                                          |
| U4  | typography-and-punctuation      | 62 (33 on human prose) | `em/en dash` ships as **FAIL**                                                                  | downgrade to WARN by default. The evidence does not support a hard cut.                                                                                                                                                                |
| U5  | self-answered-question          | **0**                  | ships as FAIL                                                                                   | probe before next release; zero support in 2,632 observations                                                                                                                                                                          |

---

## 7. Confidence calibration

| confidence | n calls | % of calls | accuracy | 95% CI     |
| ---------- | ------- | ---------- | -------- | ---------- |
| 1          | 0       | 0.0%       | n/a      | n/a        |
| 2          | 2       | 0.3%       | 50.0%    | 9.5-90.5   |
| 3          | 161     | 28.0%      | 97.5%    | 93.8-99.0  |
| 4          | 194     | 33.7%      | 100.0%   | 98.1-100.0 |
| 5          | 219     | 38.0%      | 100.0%   | 98.3-100.0 |

Calibration is monotone and, at the top, perfect: **413 calls at confidence 4-5, 413
correct.** All five errors in the sweep sit at low confidence -- one at
confidence 2, four at confidence 3. This is not an instrument whose confidence-5 calls are 60%
accurate; the opposite. It is also further evidence of saturation -- an instrument that
is never wrong when it is sure, on a task where it is sure 72% of the time, is not being
asked a hard question.

Note the confidence signature by verdict: `human` calls average **4.88** confidence and
`ai` calls **3.82** (on the human-control arm alone, mean confidence is 4.95). The judge is _more_ certain when it says human. That is consistent with the
control passages carrying positive, hard-to-fake evidence -- typos, scrape artifacts,
named signatories, dead ends reported as dead ends -- while `ai` is the residual verdict
reached by absence.

---

## 8. Inter-judge agreement

| comparison                                 | n pairs | raw agreement | expected by chance | Cohen's kappa | PABAK |
| ------------------------------------------ | ------- | ------------- | ------------------ | ------------- | ----- |
| cross-pass, one pair per item              | 198     | 98.0%         | 62.7%              | **0.946**     | 0.960 |
| cross-pass, all pairs                      | 288     | 97.9%         | 63.9%              | 0.942         | 0.958 |
| within-pass replicates (4 doubled batches) | 96      | **100.0%**    | 61.5%              | 1.000         | 1.000 |
| cross-pass, machine arms only              | 151     | 97.4%         | 97.4%              | **-0.010**    | 0.948 |
| cross-pass, human-control only             | 47      | 100.0%        | 100.0%             | undefined     | 1.000 |

Confusion, one pair per item: ai|ai 147, ai|human 1, human|ai 3, human|human 47.

The machine-arms-only kappa of -0.010 is the base-rate paradox, not disagreement: both
passes call nearly everything `ai` there, chance-expected agreement is itself 97.4%, and
the correction consumes the entire signal. PABAK is reported beside it for that reason.
**The headline numbers can be read at face value: agreement is 98.0% across passes and
100.0% between two independent dispatches of the same batch.** The judgments are not
noise. They are, if anything, too consistent to be informative.

---

## 9. Limitations, stated in full

**Single judge family.** Every one of the 576 calls came from the same model family that
generated the machine arms and wrote the corpus. There is no second opinion in this
sweep from any other lineage. Cross-pass agreement of 98.0% measures self-consistency,
not accuracy, and self-consistency within one family is the cheapest kind.

**Judges and generators share a lineage.** A model detecting its own family's output is
the easiest possible version of the task, and it is not the task the pipeline exists to
survive. The 100.0% detection on raw-ai should be read as "this family recognizes itself"
rather than "this text is detectable".

**The corpus was written by the agent family being tested.** The raw-ai, humanized and
gate-clean passages were authored by the same lineage doing the judging. Any regularity
that family produces and also notices is double-counted here. The human-control arm is
the one part of the corpus not subject to this: it is verbatim pre-2021 text (Wikipedia
_Signpost_, SQLite docs, ripgrep README, NSF notices and similar), pinned to revision ids
with timestamps on or before 2020-12-31, fetched as raw bytes rather than transcribed.
That provenance is documented per-passage in `corpus/*/human-control/PROVENANCE.md`.

**No commercial detector in the loop.** Not GPTZero, not Originality.ai, not Turnitin,
not Pangram. Every number here describes how an LLM judge behaves. Nothing here licenses
a claim about how a deployed commercial classifier would score the same items, and the
pipeline's actual adversary is the latter.

**Failed and duplicated batches -- exact counts.** 24 judgment files, 576 calls, exactly
the planned number, so no calls were lost. But the dispatch had an off-by-one and **4
batches were never judged (P1-B12, P2-B03, P2-B10, P2-B12) while 4 were judged twice
(P1-B01, P2-B01, P2-B05, P2-B11)**. 96 calls (16.7% of the sweep) bought no new coverage.
Against a design in which every item is judged exactly twice, what actually happened was:

| calls received | items |
| -------------- | ----- |
| 0              | 6     |
| 1              | 72    |
| 2              | 132   |
| 3              | 72    |
| 4              | 6     |

282 of 288 items were judged at least once; **6 were never judged at all**; only 198 were
judged by both passes, which is the denominator for every agreement figure. A batch is a
seeded random draw, so the misallocation is unbiased across arm and treatment in
expectation -- it thins some cells and thickens others rather than tilting a comparison
systematically -- but cell sizes in the cross-tabs are correspondingly uneven and are
printed with every rate for that reason.

**Ceiling effect.** The dominant limitation. Detection is at 98.8% on machine arms and
0.0% on control. Minimum detectable difference at 80% power for the chunk contrast is
~3.6 pp, and in the raw-ai arm no effect of any size is detectable. Every null in this
document is a ceiling null.

**Markdown block confound.** Word identity holds; block structure does not. `as-authored`
is the only treatment with undamaged markdown, and judges cited reflow damage on the
other three (chunk 2, punchy 8, irregular 5, as-authored 0). Section 4.

**Composition contamination in every pooled marginal.** Because the control arm is at a
floor and the machine arms at a ceiling, any table pooled across arms is close to a
restatement of arm composition. The pooled treatment marginals actually reverse the sign
of the within-arm comparison. Only arm-conditional tables should be quoted from this
document.

**Clustering is regex over the judges' prose, not over the underlying text.** 31 clusters,
multi-label, hand-written patterns; **34.8% of the true-tell pool (915 of 2,632 strings)
matched nothing** and is sampled verbatim rather than dropped. Cluster counts are
citation incidences, so a verbose judge can inflate one; distinct-item counts are given
beside every cluster for that reason. The cluster-to-gate-rule mapping in
`RESULTS.json:gate_cross_reference` is hand-built and is the least mechanical thing in
this analysis.

**Zero false positives means the false-tell deliverable is unfilled.** Restated here so
it is not lost: the ranked "false tells" list the brief asked for does not exist in this
data, and the discrimination-ratio table in section 5.1 is a substitute derived from the
human-evidence pool, not a measurement of misclassification.

---

## 10. What to do next

1. **Re-run against a judge that is not saturated.** A commercial detector, or an LLM
   judge from a different lineage, or the same judge with a forced-quota rubric. Nothing
   about the pipeline can be measured until the instrument has range.
2. **Strip markdown before applying paragraphing treatments.** Removes the section-4
   confound outright.
3. **Fix the dispatch off-by-one and re-judge P1-B12, P2-B03, P2-B10, P2-B12** -- 96
   item-slots, including the 6 items that have never been judged.
4. **Implement U1 (tricolon), then new tells 1, 2, 5 and 9.** Those four are computable,
   safe by the discrimination ratio, and between them they touch 441 strings (16.8%) of the
   true-tell pool; adding U1 brings the set to 750 strings (28.5%), more than the entire
   ENCODED rule set touches today.
5. **Do not implement performed-hedging. Downgrade the em-dash FAIL. Probe the
   self-answered-question rule.** Section 5.1.
6. **Spend the next sweep on `social` and `howto` at long length.** That is where every
   escape happened and the only place gate-clean detection drops below 95%.
