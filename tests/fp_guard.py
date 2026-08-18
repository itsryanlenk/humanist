#!/usr/bin/env python3
"""False-positive guard: sweep the checker over known-human prose and fail if it
blocks too much of it.

This is the most important test in the repository, and it exists because the rule
set this project was built from failed it catastrophically. Swept over these same
24 documents, the previous version raised 919 FAILs and blocked 22 of 24. 94.6% of
those failures came from two rules about typography rather than writing.

A checker that fails nine of ten published essays is not measuring what it claims
to measure, and worse, it teaches its users to ignore the number. So the ceiling
below is a hard CI gate: any rule change that pushes the false-positive rate back
up fails the build, and no amount of "but the rule is correct in principle"
overrides a measurement.

  python tests/fp_guard.py            # enforce the ceilings
  python tests/fp_guard.py --report   # print the full per-document breakdown

The corpus (tests/fp-corpus/) is 24 documents, ~107k words, published 1854-2018,
across four registers: narrative and essay, journalism, technical standards, and
legal or institutional. Every document is public domain or freely redistributable,
and _manifest.json records author, publication year, source URL and exact slice for
each. Its known limitation is register skew: it is heavy on pre-1920 literature,
so it over-samples a formal register and under-samples contemporary conversational
writing. It is evidence about one slice of human prose, not all of it.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "humanist" / "skills" / "humanist"
CORPUS = ROOT / "tests" / "fp-corpus"
sys.path.insert(0, str(SKILL))

import humanist  # noqa: E402

# --- The ceilings. Lower them when you improve the rules; never raise them to
# make a change pass. Raising one is a decision that belongs in a pull request
# with an argument attached, not a quiet edit.
MAX_FAILS_PER_1K = 0.60
MAX_BLOCKED_FRACTION = 0.25
MAX_SINGLE_RULE_SHARE = 0.40   # no one rule may dominate the failures


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true", help="print the per-document breakdown")
    args = ap.parse_args()

    if not CORPUS.is_dir():
        print(f"ERROR: corpus missing at {CORPUS}", file=sys.stderr)
        return 2
    docs = sorted(p for p in CORPUS.glob("*.md"))
    if not docs:
        print(f"ERROR: no documents in {CORPUS}", file=sys.stderr)
        return 2

    manifest = {}
    mpath = CORPUS / "_manifest.json"
    if mpath.exists():
        for entry in json.loads(mpath.read_text(encoding="utf-8")):
            manifest[entry["file"]] = entry

    house = dict(humanist.HOUSE_CONFIG)
    total_words = total_fails = total_warns = 0
    blocked = []
    rule_counter = Counter()
    rows = []

    for doc in docs:
        raw = humanist.read_text(str(doc))
        res = humanist.analyze(raw, house)
        total_words += res["words"]
        total_fails += res["fails"]
        total_warns += res["warns"]
        if res["fails"]:
            blocked.append(doc.name)
        for rid, _name, sev, n, _ex in res["findings"]:
            if sev == "FAIL":
                rule_counter[rid] += n
        rows.append((doc.name, res["words"], res["fails"], res["warns"], res["grade"]))

    per_1k = (total_fails / total_words * 1000) if total_words else 0.0
    blocked_frac = len(blocked) / len(docs)
    top_rule, top_n = (rule_counter.most_common(1) or [("none", 0)])[0]
    top_share = (top_n / total_fails) if total_fails else 0.0

    if args.report:
        meta = manifest.get(rows[0][0], {})
        print(f"{'document':38} {'words':>7} {'FAIL':>5} {'WARN':>5} {'FK':>5}")
        for name, w, f, wn, g in rows:
            print(f"{name:38} {w:7,} {f:5} {wn:5} {g:5.1f}")
        print()
        if rule_counter:
            print("FAILs by rule:")
            for rid, n in rule_counter.most_common():
                print(f"  {rid:26} {n:5}  ({n / total_fails:.1%} of all failures)")
            print()
        if meta:
            print(f"corpus sample entry: {meta.get('author')}, "
                  f"{meta.get('published')} - {meta.get('title')}")

    print(f"corpus       {len(docs)} documents, {total_words:,} words, "
          f"published 1854-2018")
    print(f"failures     {total_fails} FAIL, {total_warns} WARN")
    print(f"density      {per_1k:.2f} FAIL per 1,000 words   (ceiling {MAX_FAILS_PER_1K})")
    print(f"blocked      {len(blocked)}/{len(docs)} = {blocked_frac:.1%}"
          f"   (ceiling {MAX_BLOCKED_FRACTION:.0%})")
    print(f"top rule     {top_rule} at {top_share:.1%} of failures"
          f"   (ceiling {MAX_SINGLE_RULE_SHARE:.0%})")

    problems = []
    if per_1k > MAX_FAILS_PER_1K:
        problems.append(f"failure density {per_1k:.2f}/1k exceeds the ceiling of {MAX_FAILS_PER_1K}")
    if blocked_frac > MAX_BLOCKED_FRACTION:
        problems.append(f"{blocked_frac:.1%} of human documents blocked, ceiling "
                        f"{MAX_BLOCKED_FRACTION:.0%}: {', '.join(blocked[:6])}")
    if top_share > MAX_SINGLE_RULE_SHARE and total_fails > 10:
        problems.append(f"rule '{top_rule}' produces {top_share:.1%} of all failures; "
                        "one rule dominating the output is how a checker stops being read")

    if problems:
        print("\nFP GUARD FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("\n  Run with --report for the per-document and per-rule breakdown.",
              file=sys.stderr)
        return 1

    print("\nFP GUARD PASSED: the checker leaves known-human prose alone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
