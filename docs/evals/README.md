# Evaluations

Two studies stand behind this repository's claims. Both are described here in
enough detail to rebuild, and both are reported with the results that went against
the hypothesis as well as the ones that supported it.

- **[detection-sweep-synthesis.md](detection-sweep-synthesis.md)** — the analyst's
  full narrative, including the power analysis, the confound, the discrimination
  ratios and proposed rule text for every new tell. **Where this summary and that
  document disagree, that one is right**: two claims on this page were corrected
  against it after first publication.
- **[detection-sweep.md](detection-sweep.md)** — the generated tables behind it.
  576 judgments over 282 passages. The headline finding is negative and it
  reshaped the project.
- **[length-test.md](length-test.md)** — study 2. Does a longer document hide a
  generated one? 56 blinded judgments over the same essay presented whole and in
  slices. Also negative, and it bounds its own claim honestly.
- The false-positive audit that drove the rule recalibration is reproducible
  directly: `python tests/fp_guard.py --report`.

---

## Study 1: does the pipeline make prose read as human?

### Design

A four-arm factorial sweep, judged blind.

- **Arms (4):** raw AI draft · after the rewrite pass · after every checker FAIL
  was fixed · genuine human prose published before 2021.
- **Paragraphing treatments (4):** as authored · every paragraph break removed ·
  broken into one-to-two-sentence paragraphs · irregular, seeded-random paragraph
  lengths. **Word-identical by construction**, verified: all 288 items match their
  source after whitespace normalization. That holds at the token level but not at
  the markdown *block* level, which turned out to matter. See the confound in
  Result 3.
- **Registers (6):** essay · how-to · social · marketing · email · review.
- **Lengths (3):** ~150, ~400, ~900 words.

72 source passages, 288 blinded items, two independent judging passes. Judges saw
one passage at a time with no context, no filenames encoding condition, and no
access to the key. They returned a forced binary, a 1–5 confidence, and — the
actual product — the specific quotable features that drove the call.

### Result 1: the instrument is sharp

|                                        |              |
| -------------------------------------- | ------------ |
| False positives on genuine human prose | **0 of 143** |
| Mean confidence on human prose         | 4.95 / 5     |
| Cross-pass agreement (Cohen's kappa)   | **0.946**    |
| Overall accuracy                       | 99.1%        |

This matters more than any other number here. A judge that flagged human writing
would make everything else unreadable. This one did not, once, and two independent
passes agreed almost perfectly. The measurement is not noise.

### Result 2: the pipeline barely moves detection

| arm                         | detected as machine |
| --------------------------- | ------------------- |
| raw AI draft                | 100.0%              |
| after the rewrite pass      | 98.6%               |
| after the checker was clean | **97.8%**           |
| genuine human prose         | 0.0%                |

**No effect detected.** Prose a careful mechanical checker calls clean is still
identified as machine-written 97.8% of the time by a blind reader. The 100% to
97.8% difference is smaller than the roughly 3.6 points this design could resolve
at 80% power, so the honest phrasing is "no effect detected", not "an effect of
-2.2 points". The instrument is not blunt, it is saturated: pinned to 0% on one
rail and 98.8% on the other, reliable and uninformative at the same time, which is
a specific failure mode rather than a good result.

Stated plainly, because it is the thing most worth knowing about this project:
**"undetectable" is not on the table, and nothing in this repository should be
read as offering it.** What the pipeline delivers is better prose. That is worth
having on its own terms, and it is a different thing.

### Result 3: the paragraphing hypothesis did not survive

The study was designed around a specific prediction: that stripping paragraph
breaks makes machine prose markedly easier to spot.

The pooled rates across all four arms look like this, and **they must not be
quoted**:

| treatment   | pooled    | share of its calls that are human-control |
| ----------- | --------- | ----------------------------------------- |
| as authored | 74.6%     | 23.2%                                     |
| one chunk   | **71.9%** | **27.5%**                                 |
| punchy      | 75.2%     | 24.8%                                     |
| irregular   | 75.7%     | 23.6%                                     |

Read naively that says chunk is detected *least*, the opposite of the hypothesis.
It says nothing of the kind. With the control arm pinned at 0% and the machine
arms at 97-100%, a treatment's pooled rate mostly restates how many control calls
landed in it, and the lost batches made those shares unequal. Chunk carries the
largest control share and therefore the lowest pooled rate. That is a textbook
composition artifact, and it points the wrong way.

The interpretable version is machine arms only:

| treatment   | machine arms | n   |
| ----------- | ------------ | --- |
| as authored | 97.2%        | 106 |
| one chunk   | **99.1%**    | 111 |
| punchy      | 100.0%       | 106 |
| irregular   | 99.1%        | 110 |

So chunk moves **+1.0 points in the hypothesized direction**, not against it. But
that is below the ~3.6 points this design can resolve, and the sign is not
consistent across arms: +4.5 in gate-clean, -1.2 in humanized, flat at the rails in
the other two. An effect that appears only in aggregate is a composition artifact;
an effect that appears in one of four arms on a hundred calls is a coin.

**A confound the judges found for us.** They cited 15 features describing damage
the re-paragraphing itself introduced: headings fused into the following sentence,
code fences run together, tweet numbers welded to the previous line. By treatment:
chunk 2, punchy 8, irregular 5, **as-authored 0**. Word identity holds at the token
level, but whitespace normalization does not preserve markdown *block* structure,
so each of the three synthetic treatments carries a small artificial tell the
hypothesis never intended. The direction makes the null stronger rather than
weaker, since the artifact should have inflated detection on exactly those three,
and the observed gap is small enough that the artifact alone could account for all
of it.

The honest verdict is **not supported by this data**, and the honest caveat is that
a saturated instrument cannot rule the effect out either. What this design can
conclude is narrower and worth stating exactly: no paragraph-shape effect larger
than roughly 4 points exists on machine text this judge already catches 98.8% of
the time. A real test needs a judge that is not at the ceiling, not a bigger
sample. And next time, strip markdown to plain prose *before* applying the
treatments.

### Result 4: why the pipeline barely helps — the useful finding

Judges cited 3,522 features. Clustering them and cross-referencing against the
checker's rule set explains why the pipeline could not move the number:

| tell                   | raw | rewritten | checker-clean | encoded? |
| ---------------------- | --- | --------- | ------------- | -------- |
| uniform beat rate      | 60  | 95        | **101**       | no       |
| aphoristic closer      | 38  | 59        | **61**        | no       |
| contraction uniformity | 21  | 36        | **43**        | partly   |
| typography             | 114 | 68        | 48            | yes      |
| AI vocabulary          | 70  | 1         | **0**         | yes      |
| negative parallelism   | 80  | 58        | 47            | yes      |

**The pipeline crushes every tell it encodes and grows the ones it does not.**
A subtractive rewrite makes prose more uniformly well-shaped, and uniform good
shape is itself what gives it away.

Ten tells were named repeatedly and have no rule at all. Ranked by citations on
correct calls, and filtered by discrimination ratio (how often judges cited a
construction as machine evidence against how often they cited it as *human*
evidence): uniform beat rate (256 cites, ratio 13.9), aphoristic closer (158,
10.3), too-complete-no-friction (137, 11.2), planted-detail callback (39),
numbers-as-texture (18), balanced clause symmetry / chiasmus (38), genre-template
completion (20), feature-benefit lockstep (16), internal arithmetic failure (12),
canonical entity list (2). Two more are only partly covered and rank at the very
top: tricolon and triads (329, ratio 35.8, the most-cited tell overall) and
announced thesis (198, ratio 64.6, the safest of all).

**One heavily-cited construction did not survive vetting and must not be encoded:
performed hedging.** It drew 137 citations as machine evidence and 50 as human
evidence, a ratio of 0.89, meaning judges reached for it about equally in both
directions. A rule built on it would fire on careful human writing. The same test
retired two rules this checker used to enforce: typography and punctuation (ratio
0.61) and the self-answered question (0.00, cited *only* as human evidence).

With zero false positives in the study there is no measured set of tells that
misfire on human prose, so this ratio is an honest substitute for that deliverable
rather than the deliverable itself.

All of them are rhythmic and structural. The checker is almost entirely lexical.
That gap is the project's real backlog, and every one is now written up as a
read-aloud check in `ai-tropes.md` under "The rhythm tells."

### Reproducing

72 passages, four treatments each, opaque IDs assigned by a seeded shuffle with
the key held separately, two partitions into twelve batches with different seeds
so no two items travel together twice. Judge blind, forced binary plus confidence
plus quoted features, then join to the key and tally.

## Honest caveats

- **Judges and text come from one model family.** The corpus author, the
  rewriter and the judges are all agents of the same lineage. A judge detecting
  its own family's output is the easiest version of this task, and a different
  model, a commercial detector, or a human reader could all give different
  numbers. This is the largest limitation and it is not small.
- **No commercial detector was in the loop.** No API key was available. The
  detection rates here are against an LLM judge and generalize to nothing else
  without testing.
- **Four batches were dispatched twice and four not at all**, from an off-by-one
  in the harness. It cost 0 of 576 planned calls but thinned specific cells: 282
  of 288 items were judged, 6 never were, and 198 were seen by both passes.
- **The human-control arm is pre-2021 published prose** across six registers.
  It is a small sample per cell.
- **Detection is at ceiling in the machine arms**, so several planned contrasts
  (paragraphing above all) cannot be resolved by this design.


---

## Study 2: does length hide a generated document?

The one variable with a gradient in study 1 was length: gate-clean detection sat at
98-100% for short and medium passages and 95.1% for long ones, and every passage
that escaped was long-form. So: take one generated 2,940-word essay, show it to one
panel whole and to another panel as six standalone ~490-word slices. Same words,
verified by assertion. Any difference is presentation length alone.

| | detected | mean confidence |
| --- | --- | --- |
| whole document (n=8) | **8/8** | 4.25 |
| slices (n=24) | **24/24** | 4.17 |
| human control, both arms (n=24) | **0/24** | 5.00 |

**Not supported**, and the honest bound matters: this design could only have
resolved a difference of **38 percentage points** of detection or 0.42 points of
confidence. Anything smaller is invisible at this n. The item was also 17,292
characters, about 64% of the intended length, so this is a floor result on a
document that is merely long-ish.

Three things worth carrying forward:

**The dilution is real in the self-reports; it just did not change the verdict.**
Half the whole-arm judges admitted reduced attention on part of the document while
claiming full coverage, and three of four named *the same passage* — the stretch of
thematic filler doing no argumentative work. If length can hide anything, that is
where.

**Length supplied evidence rather than concealing it.** The essay's closing line
claimed it had spent "five thousand words"; it had spent 2,940. That single false
claim was the decisive quote for 5 of 8 whole-document judges. The same sentence
sits inside a slice, where it is not self-contradictory, because a 518-word excerpt
can plausibly belong to a longer piece. Only the whole document can be counted.

**Judges decide early on human prose and late on machine prose.** All 8 decisive
quotes on the human document fell in its first 18.4%, six of them citing the same
sentence. On the generated document the mean decisive position was 86% and the
median 98.5%. Human writing announces itself; machine writing has to be read to the
end.

One tell in that study was manufactured by the harness rather than the generator:
the blinding step stripped markdown headings, which left a cross-reference to
"section II" dangling in a document that no longer had visible sections. All eight
judges flagged it. It is discounted in the report.
