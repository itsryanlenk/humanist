---
name: ship-gate
description: |
  The release gate for public prose. Runs every quality gate in a fixed order before
  a draft ships, and refuses to call a draft ready while any gate is unrun. Use
  before publishing or handing over anything a reader will see: a blog post, a web
  page, a newsletter, a product listing, release notes, a social post, a client
  deliverable. Trigger phrases include "is this ready to ship", "run the gates",
  "final check before publishing", "ship gate", "red team this", "check this before
  it goes live". Orchestrates the humanist rewrite pass, the humanist.py checker,
  the composition read and an adversary pass that attacks the claims, then writes a
  gate report. It does not edit the draft on its own authority and it does not
  publish anything.
---

# Ship gate: no draft is ready until every gate has a result

The `humanist` skill makes a draft read better. This skill decides whether it may
ship. The two jobs are different. A draft can read well and still carry a wrong
number, a stale figure or a claim nobody checked.

**The one rule.** A gate that did not run is a failed gate. A missing tool, a
broken shell, a deadline or a long session never turns "not run" into "pass".

## Why this exists

Every gate in a prose pipeline is a step that someone has to choose to do. Under
pressure the gates get skipped, and the skip gets reported as a tooling problem or
not reported at all. The draft then reaches the reader with the one defect the
skipped gate would have caught.

This skill makes a skip visible. Each gate must end with one of three results, and
the draft carries its status in its own name until all of them pass.

## The gates, in order

Run them in this order. Each one assumes the ones before it ran.

| # | Gate | What it catches | How it runs |
|---|---|---|---|
| 1 | Rewrite pass | Machine residue, filler, inflated significance | `../humanist/SKILL.md` step 1 |
| 2 | Checker | Mechanical tells, banned constructions, dashes | `../humanist/humanist.py` |
| 3 | Composition read | Rhythm tells no pattern catches | `../humanist/SKILL.md` step 3 |
| 4 | Adversary, lens A | Wrong claims, missing bases, weak sources | A subagent with `adversary.md` |
| 5 | Adversary, lens B | What lens A missed, and defects its fixes added | A second, fresh subagent |
| 6 | Re-measure | Anything the fixes from gates 4 and 5 broke | Gate 2 again, on the final text |
| 7 | Render check | Copy that is correct in the file and wrong on the page | Open the published surface or its preview |

Gate 7 applies when the draft goes into a CMS, a template or any system that
changes what the reader sees. A plain file handed over as-is skips it, and the
report says so.

### Gate 2 details

```bash
python ../humanist/humanist.py draft.md --strip-quotes
```

Ship at zero FAIL. Judge each WARN. For web copy, extract the body first with
`../humanist/tools/html2prose.py`, as the humanist skill describes. Exit code 2
means the checker did not run. Record it as NOT RUN, never as a pass.

### Gates 4 and 5: the adversary

The adversary is a subagent. It receives the draft, the primary sources the draft
cites, and `adversary.md`. It does not receive the drafting conversation.

An adversary that knows why each choice was made will defend those choices. That is
the failure this gate exists to prevent.

Run it twice, with fresh context each time and a different lens each time:

- **Lens A, the skeptic.** Runs every pass in `adversary.md`.
- **Lens B, the fact checker.** Verifies every number, date, quote and named source
  against the primary sources, one by one.

The second run is not redundant. Fixes made after the first run add new defects: a
length limit breached by an added sentence, or a new claim with no source. The
second run and the re-measure in gate 6 exist to catch those.

Verify a blocker yourself before you act on it. A subagent can invent a mechanism
too.

## When a tool fails

Each gate names a job. The usual tool is one way to do that job. When the tool
fails, do the same job another way.

| Failure | What to do |
|---|---|
| The checker cannot run where the draft lives | Copy the draft and the checker to a place where Python runs, and run it there. |
| No subagent is available | Start a fresh session that holds only the draft, the sources and `adversary.md`. |
| The preview cannot render | Mark gate 7 NOT RUN and say so in the report. Do not describe the page as checked. |
| Nothing works | Stop. Report the gate as NOT RUN with the exact error text. Do not ship. |

Report the exact error message, not a summary of it. A summary hides whether the
failure was real and whether a fallback existed.

## Time pressure

When time runs short, cut scope. Never cut gates.

Ship fewer changes with every gate passed, or stage all of them marked NOT READY
with the owed gates listed. Both are acceptable. A draft marked ready with gates
unrun is not.

## The status label

Until every gate passes, the draft carries **NOT READY** in the place a reviewer
will see first: the file name, the CMS title or the first line of the handoff. The
person approving it should not have to read a report to learn that it failed.

Remove the label only when the gate report shows every gate as PASS or as N/A with
a reason.

## The gate report

End every run with this block. Put it at the top of any handoff.

```
SHIP GATE: READY | NOT READY
Draft: <file or URL>
Run at: <date and time, from a checked clock>

| # | Gate            | Result  | Evidence                              |
|---|-----------------|---------|---------------------------------------|
| 1 | Rewrite pass    | PASS    | <what changed, in one line>           |
| 2 | Checker         | PASS    | 0 FAIL, 3 WARN judged                 |
| 3 | Composition     | PASS    | <what the read changed>               |
| 4 | Adversary A     | FIX     | 2 blockers, both fixed                |
| 5 | Adversary B     | PASS    | 0 blockers                            |
| 6 | Re-measure      | PASS    | 0 FAIL after fixes                    |
| 7 | Render check    | NOT RUN | <exact error text>                    |

Owed before ship: <every NOT RUN gate, with its fallback>
```

Allowed results: PASS, FAIL, FIX (blockers found and fixed), N/A (with a reason)
and NOT RUN (with the exact error). A report with any FAIL or NOT RUN is NOT READY.

## What this skill must never do

- Never report a draft as ready while any gate is NOT RUN.
- Never let a deadline decide which gates run.
- Never give the adversary the drafting history.
- Never edit claims on its own authority. Blockers go to the author, who decides.
- Never publish. The person who owns the surface publishes.
