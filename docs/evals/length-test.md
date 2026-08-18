<!-- The analyst's report, vendored verbatim apart from local paths scrubbed and
     spelling normalized to American English. No number or judgment was altered.
     This is the authority where it and any summary disagree. -->

# Does length hide a generated document?

**Whole-vs-slice detection of one generated essay, 56 blinded judgments, 16 judges.**

Lab: `<lab>`
Script: `len_tally.py` → `len_tally_out/{len_tally_report.txt, summary.json, records.json}`
Origin key: `LENKEY.json` (seed 20260818). All numbers below are exact counts from the joined records, not estimates.

The question: my generated 2,940-word essay was cut into six standalone ~490-word slices. The same words were shown to two independent panels — one panel saw the whole document, the other saw only individual slices with no indication they belonged together. If judges dilute their attention across a long document, the slices should be caught more often, or more confidently, than the whole.

---

## 0. Read the control first

**Human prose was never called AI. Not once, in either arm.**

| Arm        | Human judgments | Called AI | FP rate  | 95% CI (exact)   |
| ---------- | --------------- | --------- | -------- | ---------------- |
| WHOLE      | 8               | 0         | 0.0%     | 0.0% – 36.9%     |
| SLICE      | 16              | 0         | 0.0%     | 0.0% – 20.6%     |
| **Pooled** | **24**          | **0**     | **0.0%** | **0.0% – 14.2%** |

Every one of those 24 human calls was made at confidence 5 of 5 (sd = 0.000). The human items were: Du Bois, _The Souls of Black Folk_ ch. 1 (whole, 2,966 w, and a 512-word excerpt); Russell, _Political Ideals_ ch. 1 (512-word excerpt); and a 541-word unedited human rant.

This matters for reading everything below. A detector with a nonzero false-positive rate can manufacture a high detection rate by calling everything AI. This one did not — it separated the classes cleanly at maximum confidence in both directions. But note the ceiling problem it creates: with 0/24 false positives and 32/32 true positives, **the discrimination task was too easy for this judge pool, and nothing in the experiment is near the region where a length effect could show up as an error.**

The upper CI bounds are the honest caveat. With only 8 human whole-document judgments, a true false-positive rate as high as ~37% is still consistent with observing zero.

---

## 1. The primary contrast: whole vs. slices

|                            | Detected as AI | Rate   | 95% CI (Wilson) | 95% CI (exact) | Mean confidence  |
| -------------------------- | -------------- | ------ | --------------- | -------------- | ---------------- |
| **WHOLE** (2,895 w, n=8)   | 8 / 8          | 100.0% | 67.6 – 100%     | 63.1 – 100%    | 4.250 (sd 0.463) |
| **SLICE** (6 slices, n=24) | 24 / 24        | 100.0% | 86.2 – 100%     | 85.8 – 100%    | 4.167 (sd 0.482) |

**Two-proportion test:** difference = +0.0 pp. The pooled standard error is exactly zero (no variance in either arm), so the z statistic is **undefined**, not merely non-significant. Reporting a z here would be fabricating a number. Fisher's exact test on the 2×2 gives **p = 1.0000**.

**Permutation test on confidence** (200,000 relabelings, seed 20260818):

- observed difference (SLICE − WHOLE) = **−0.0833** confidence points
- two-sided **p = 1.0000**
- null 95% band = [−0.4167, +0.4167]

The point estimate runs _against_ the dilution hypothesis: judges were very slightly **more** confident on the whole document than on its slices. The difference is a twelfth of a scale point and is indistinguishable from noise.

Confidence CIs: WHOLE mean [3.863, 4.637] (t) / [4.000, 4.625] (bootstrap); SLICE mean [3.963, 4.370] (t) / [4.000, 4.375] (bootstrap). They overlap almost entirely.

### Verdict on attention dilution

**NOT SUPPORTED, and for effects below the resolution floor, UNRESOLVABLE at this n.**

Slices were not detected more often (both arms at 100%) and were not detected more confidently (−0.08 points, wrong direction, p = 1.0).

### What this n could actually have resolved

This is the number that bounds the claim. Holding the slice arm at its observed 24/24, I computed the Fisher exact p for every possible whole-arm result:

| WHOLE result | Rate      | Fisher p                       |
| ------------ | --------- | ------------------------------ |
| 8/8          | 100.0%    | 1.0000                         |
| 7/8          | 87.5%     | 0.2500                         |
| 6/8          | 75.0%     | 0.0565                         |
| **5/8**      | **62.5%** | **0.0113 ← first significant** |
| 4/8          | 50.0%     | 0.0019                         |

**Minimum resolvable detection difference: 38 percentage points.** The whole document would have had to escape detection roughly 3 times in 8 before this design could call the difference real. Any true dilution effect smaller than ~38 pp is invisible here.

**Minimum resolvable confidence difference: 0.42 scale points** (the edge of the permutation null band). The observed −0.08 is a fifth of that.

So the correct statement is not "length does not help." It is: **length does not help by 38 points of detection or 0.42 points of confidence. Anything smaller, this experiment cannot see.**

---

## 2. Per-slice detection: nothing escaped

| Slice | Token   | Source paras | Words | Detected | Mean conf |
| ----- | ------- | ------------ | ----- | -------- | --------- |
| 1     | LN-9319 | 0–4          | 436   | 3 / 3    | 4.00      |
| 2     | LN-5527 | 5–10         | 491   | 4 / 4    | 4.00      |
| 3     | LN-2735 | 11–16        | 495   | 5 / 5    | 4.40      |
| 4     | LN-5996 | 17–21        | 490   | 5 / 5    | 4.40      |
| 5     | LN-8343 | 22–27        | 465   | 4 / 4    | 4.00      |
| 6     | LN-4743 | 28–36        | 518   | 3 / 3    | 4.00      |

**No slice escaped. There are no escape quotes to report** — every generated slice was called AI by every judge who saw it, 24 for 24. The lowest single confidence recorded anywhere in the generated set was a 3 (S4 on slice 5); everything else was 4 or 5.

This is itself informative about what the judge uses. If the tells lived in document-level structure — the four-proposition recap, the section architecture, the overall arc — then a 490-word window with the scaffolding cut away should have been survivable at least once. It was not. **The tells are local: they are in the sentence engine, and they are present in every 500-word window of the document.** The recurring cited features across slices are the negative-parallelism frame ("It is not X. It is Y."), vague-attribution empiricism, stock exemplars, and the absence of any lived, specific, first-person texture. None of those require a long document to see.

---

## 3. Where in the document judges decided

This is the most useful output, and it did not come out the way the framing predicted.

Position = character offset of each judge's `decisive_quote` within the item they actually saw, as a fraction of that item's length.

| Arm / origin             | n   | First third | Middle third | Final third | Mean pos  | Median pos |
| ------------------------ | --- | ----------- | ------------ | ----------- | --------- | ---------- |
| WHOLE / human (Du Bois)  | 8   | **8**       | 0            | 0           | 13.9%     | 18.4%      |
| WHOLE / mine (generated) | 8   | 0           | 2            | **6**       | **86.0%** | **98.5%**  |
| SLICE / mine             | 24  | 3           | 5            | 16          | 65.8%     | 68.2%      |
| SLICE / human            | 16  | 1           | 10           | 5           | 59.9%     | 64.8%      |

**On the human document, judges decided early — every single time.** All 8 decisive quotes fall in the first 18.4% of the text. Six of eight cite the same passage (the double-consciousness sentence); the other two cite the schoolhouse visiting-card anecdote a few hundred words earlier. Judges recognized Du Bois within one or two sentences and spent the remaining 2,700 words confirming, not deciding.

**On the generated document, judges decided at the very end.** Six of eight decisive quotes sit at 98.5–98.9% of the document — the closing paragraph. Five of them quote the same sentence:

> "I will close this document and open a feed engineered to hold my attention, having just spent five thousand words explaining why I should not. That is not hypocrisy. It is the thesis."

The document is 2,940 words. It claims to be five thousand. **That is a self-consistency failure that only exists at whole-document scale**, and it is what decided the long-form call for the majority of the panel.

So the "judges decide early, therefore length does not help" mechanism is only half right:

- **True for the human item.** Recognition happened at the opening sentence and the rest of the length was inert.
- **False for the generated item.** Length did not dilute the evidence — it _manufactured_ new evidence. The essay's own claim about its length became falsifiable only because the whole thing was in front of the reader.

The cross-check confirms it. When I map the slice-arm decisive quotes back onto whole-document coordinates, they spread evenly across the essay (first = 7, middle = 10, final = 7, mean position 50.9%). The slice judges found sufficient evidence everywhere. The whole-arm judges converged on the one place where the document contradicted itself.

**Length did not protect this document. Length gave it a longer rope.**

---

## 4. The `words_read` field — self-report, and labeled as such

Everything in this section is what the judges _said_ about their own reading. It is unverifiable, it is exactly the kind of claim a model has incentive to inflate, and it should be read as a claim rather than a measurement. Classification was done with a negation-aware matcher (an earlier pass wrongly scored "without skimming" as a skim admission; that bug is fixed in `len_tally.py`, and the whole-arm results were hand-checked against all 16 verbatim strings).

| Arm   | n   | Claim full coverage | Explicitly deny skimming | Admit skimming | **Admit reduced attention on part** | Report re-read | Report tool use | Mean length |
| ----- | --- | ------------------- | ------------------------ | -------------- | ----------------------------------- | -------------- | --------------- | ----------- |
| WHOLE | 16  | 16 (100%)           | 9 (56%)                  | 1 (6%)         | **8 (50%)**                         | 6              | 10              | 524 chars   |
| SLICE | 40  | 40 (100%)           | 7 (18%)                  | 0 (0%)         | **0 (0%)**                          | 18             | 8               | 146 chars   |

**Did whole-arm judges admit to skimming?** Almost none used the word — but **half of them (8/16) admitted reduced attention on part of the document while simultaneously claiming full coverage.** Split evenly: 4/8 on the human item, 4/8 on the generated item. In the slice arm, zero of forty made any such admission; a 490-word item does not create the opportunity.

The whole-arm admissions in their own words:

- W1 (human item): _"I identified the text as Du Bois within the first 150 words, so the long historical middle … I read at normal reading speed for confirmation rather than line-by-line forensics — the call was already settled."_
- W6 (human item): _"the back half … I read at a genuinely lower intensity … I did not, for instance, diff it against a canonical text, so a doctored sentence somewhere in the middle could have escaped me."_
- W5 (human item): _"paragraphs 3 onward were read as confirmation rather than as fresh evidence-gathering."_
- W3 (generated item): _"I moved somewhat faster through the two-trillion-galaxies passage, which is the most generic stretch."_
- W5 (generated item): _"Skimmed more lightly, though I did read every sentence: the Truman Show setup … and the galaxies/observable-universe passage, both of which I treated as texture rather than evidence."_
- W6 (generated item): _"The galaxy/grain-of-sand section I read at slightly lower attention because its content was not doing diagnostic work."_
- W7 (generated item): _"lines 47-61 (the cosmic-insignificance stretch) got one careful pass rather than two."_

The attention dilution the hypothesis predicts **is visibly present in the self-reports.** Judges say they down-weighted the generic stretches of a long document. It simply did not cost them the call, because the document leaked in the stretches they were still reading hard — and because it contradicted itself in the closing paragraph, which nobody skims.

Note also that three of the four generated-item admissions name the _same_ passage (the cosmic-insignificance / galaxies section). If a longer document is going to hide something, this experiment suggests the hiding place is the stretch that reads as thematic filler, not the beginning or the end.

---

## 5. Inter-judge agreement

| Arm   | Pairwise verdict agreement | Unanimous items | Mean \|confidence gap\| between judge pairs |
| ----- | -------------------------- | --------------- | ------------------------------------------- |
| WHOLE | 56 / 56 = **100.0%**       | 2 / 2           | 0.214 (of a possible 4)                     |
| SLICE | 75 / 75 = **100.0%**       | 9 / 9           | 0.240 (of a possible 4)                     |

Every item in the experiment was unanimous. Confidence spread was near zero: sd = 0.000 on 6 of 11 items, max 0.816 (slice 5).

**Chance-corrected agreement is degenerate here and I will not launder it.** Fleiss κ computes to 1.0000 in the whole arm, but with Pe = 0.5000 and perfect observed accuracy that number carries no information about judge reliability — when every rater assigns every item its true label, the expected-agreement term collapses and κ is arithmetic, not evidence. In the slice arm κ is not computable at all: the block design is incomplete (items received 3, 4, 5, or 7 raters). Raw agreement is the honest statistic, and it is 100% in both arms.

---

## 6. Two structural tells — one of which is my harness's fault

The whole-arm feature lists are dominated by two self-reference failures. I checked both against the unblinded source, and they are not the same kind of thing.

**"section II" — HARNESS ARTIFACT, not a generation defect.** Eight of eight whole-arm judges flagged that the essay cites "section II" while containing no sections. It does contain sections. `longform.md` has six markdown headings, including `## II. The Fire We Light Ourselves`. LENKEY normalization rule 1 drops every line starting with `#`, which deleted them during blinding. In the document as written, the cross-reference resolves cleanly. **This tell was created by my blinding pipeline and should be discounted entirely.** It was the decisive quote for 1 of 8 whole-arm judgments (W0).

**"five thousand words" — GENUINE.** The document is 2,940 words raw, 2,895 blinded. Neither is five thousand. This is a real generation defect, it was the decisive quote for 5 of 8 whole-arm judgments, and it is the single most load-bearing piece of evidence in the entire whole arm.

Both tells physically survive into slices (`section II` is inside slice 4, `five thousand words` inside slice 6), and slice judges cited them — 4 slice judgments cited the former, 2 the latter. So neither tell is exclusive to the long form. What _is_ exclusive to the long form is the ability to **falsify** the length claim by counting the document in front of you. A 518-word slice asserting membership in a five-thousand-word essay is not self-contradictory. The whole document is.

---

## 7. Limitations — read these before quoting any number above

1. **One generated document, one topic, one author.** Every "detected" in this file traces back to a single essay on chosen ignorance and machine conformity. Its tells (negative-parallelism engine, vague-attribution empiricism, stock exemplars, zero lived texture) may be idiosyncratic to how I write that topic at that length. n(documents) = 1. The 32 judgments are not 32 independent trials of the underlying question.

2. **2,940 words is well short of the ~27,000-character target that motivated the test.** The blinded item is 17,292 characters — about 64% of the intended length. **This bounds the effect at 3k words, not at 5k, and certainly not at 27k characters of sustained argument.** The dilution mechanism the test was built to probe may only engage past a length this experiment never reached. Everything above is a floor result on a document that is merely long-ish.

3. **Reading depth is self-reported and unverifiable.** Section 4 is the mechanism the whole experiment is about, and it is the weakest evidence in the file. Judges may under-report skimming, over-report thoroughness, or confabulate a reading process after the fact. The 100% "claims full coverage" figure in both arms is exactly what you would expect from a self-report instrument with no adversarial check.

4. **Judges come from the same model family as the writer.** They may be detecting family-specific fingerprints that a human reader, or a different model family, would not see. This inflates detection in both arms symmetrically, so it does not obviously bias the whole-vs-slice _contrast_, but it does mean the absolute 100% rates should not be read as a general claim about AI-text detectability.

5. **The task was too easy, so the design has no headroom.** Both arms at 100% detection and 0% false positives means the contrast was measured entirely at ceiling. A design that could detect dilution needs a document that gets caught roughly half the time, so there is room to move in either direction.

6. **The blinding pipeline injected at least one artifact.** See §6. One of the two dominant whole-arm tells was created by my own normalization. I found this one; I cannot promise there are no others.

7. **Design coverage was imperfect.** One planned slice batch (LNS-08: LN-4743, LN-4824, LN-6473, LN-8343, LN-9319) was **never judged**, and one slice item-set was judged three times instead of twice. Total slice judgments still came to the planned 40, but the per-item distribution differs from LENKEY's plan — LN-4526 got 7 judgments instead of 6, LN-4824 got 4 instead of 5, LN-9319 and LN-4743 got 3 instead of 4. This unbalances the slice arm slightly and is why Fleiss κ is not computable there. The whole arm matched its design exactly, 8 judges × 2 items.

8. **A one-sided hypothesis tested two-sided.** The dilution hypothesis is directional (slices ≥ whole). I report two-sided tests throughout, which is conservative. It does not matter here — the point estimate is in the wrong direction and p = 1.0 either way — but it would matter in a rerun with headroom.

---

## Bottom line

Human prose was called AI zero times in 24 judgments. Against that clean baseline, my generated essay was detected 8/8 as a whole and 24/24 in slices — no difference, at a design that could only have resolved a gap of 38 percentage points or 0.42 confidence points. **The attention-dilution hypothesis is not supported, and effects smaller than that floor are unresolvable here.**

The more interesting result is _where_ the decisions happened. Judges settled the human document in its first 18% and coasted; they settled the generated document in its last 2%, on a sentence where the essay miscounted its own length. Half of the whole-arm judges admitted reading parts of the long document at reduced attention — the dilution is real and self-reported — and it cost them nothing, because a long document does not only spread its evidence thinner. It also gives itself more opportunities to contradict itself.
