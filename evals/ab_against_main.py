#!/usr/bin/env python3
"""A/B the checker on this branch against the checker on main.

This is the fork's measuring instrument. Every change made on a branch is judged
against the original, on the same two corpora, with the same arithmetic, and the
delta is what gets reported rather than a fresh set of absolute numbers.

  python evals/ab_against_main.py                 # offline: rules only, both versions
  python evals/ab_against_main.py --jev           # also run the Jev read (needs TYPESAFE_API_KEY)
  python evals/ab_against_main.py --jev --limit 3 # a cheap first look: 3 documents per class
  python evals/ab_against_main.py --gate          # exit 1 if the branch got worse

BASELINE. The baseline checker is `git show <ref>:plugins/.../humanist.py`, loaded
as a separate module, so the comparison is against what is actually on main and
not against a remembered number. The ref defaults to `main`, then `origin/main`.

CORPORA. tests/fp-corpus is 24 known-human documents (107k words). tests/ai-corpus
is six machine-drafted passages with provenance. Both are committed; pass --human
and --machine to point at larger private corpora, which is what a real measurement
needs. Six documents is an existence proof, not a sample.

WHAT IS MEASURED.
  rules      FAIL and WARN density per 1,000 words and the blocked fraction, per
             class, per version. The number that matters is the SEPARATION:
             machine density minus human density. A rule change that raises both
             has not helped; one that raises the gap has.
  jev        With --jev, the texture score and every tell density from the Jev
             read, per class, plus the rank AUC of each metric for telling the
             two classes apart. AUC 0.5 is a coin; 1.0 is perfect separation.
             This is the "judge that is not saturated" the detection synthesis
             asked for as its first next step. Whether Jev IS unsaturated on
             these corpora is exactly what the number reports, and it is not
             claimed in advance.

Jev results are cached under evals/out/ by text hash and question hash, so a rerun
after a rules-only change costs nothing. Delete the cache to re-judge.

Exit 0 after printing, always, unless --gate is set: then 1 when the human
false-positive density rose or the rules separation fell against the baseline.
Exit 2 when the harness itself could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import statistics as st
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_REL = "plugins/humanist/skills/humanist/humanist.py"
SKILL = ROOT / "plugins" / "humanist" / "skills" / "humanist"
OUT = ROOT / "evals" / "out"
sys.path.insert(0, str(SKILL))

import humanist as branch  # noqa: E402
import jev_read  # noqa: E402


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------
def git_show(ref, path):
    try:
        return subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{path}"],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def load_baseline(ref):
    tried = []
    for cand in ([ref] if ref else []) + ["main", "origin/main"]:
        if cand in tried:
            continue
        tried.append(cand)
        src = git_show(cand, SKILL_REL)
        if src:
            tmp = Path(tempfile.mkdtemp(prefix="humanist-baseline-")) / "humanist_baseline.py"
            tmp.write_text(src, encoding="utf-8")
            spec = importlib.util.spec_from_file_location("humanist_baseline", tmp)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", cand],
                                 capture_output=True, text=True, encoding="utf-8").stdout.strip()
            return mod, cand, sha
    die(f"could not read {SKILL_REL} from any of {tried}. Fetch main first: git fetch origin main")


def head_sha():
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, encoding="utf-8").stdout.strip()


# ---------------------------------------------------------------------------
# Corpora
# ---------------------------------------------------------------------------
def load_corpus(d, label, limit=None):
    d = Path(d)
    if not d.is_dir():
        die(f"{label} corpus {d} is not a directory")
    manifest = {}
    mp = d / "_manifest.json"
    if mp.exists():
        for e in json.loads(mp.read_text(encoding="utf-8")):
            manifest[e["file"]] = e
    docs = sorted(p for p in d.glob("*.md") if not p.name.startswith("_"))
    if limit:
        docs = docs[:limit]
    if not docs:
        die(f"no .md documents in {d}")
    return [(p, manifest.get(p.name, {})) for p in docs]


def register_of(meta):
    r = (meta.get("register") or "").lower()
    return {"howto": "how-to"}.get(r, r) or "unspecified prose"


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def sweep(mod, docs):
    rows = []
    for path, meta in docs:
        raw = mod.read_text(str(path))
        res = mod.analyze(raw, dict(mod.HOUSE_CONFIG))
        rows.append({
            "file": path.name, "words": res["words"], "fails": res["fails"], "warns": res["warns"],
            "fail_rules": sorted({r for r, _n, s, _c, _e in res["findings"] if s == "FAIL"}),
            "t": res["t"],
        })
    return rows


def density(rows):
    words = sum(r["words"] for r in rows) or 1
    return {
        "docs": len(rows), "words": sum(r["words"] for r in rows),
        "fail_per_1k": sum(r["fails"] for r in rows) * 1000.0 / words,
        "warn_per_1k": sum(r["warns"] for r in rows) * 1000.0 / words,
        "blocked": sum(1 for r in rows if r["fails"]) / len(rows),
    }


def auc(pos, neg):
    """Rank AUC: P(score of a machine doc > score of a human doc), ties count half."""
    if not pos or not neg:
        return None
    wins = 0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return wins / (len(pos) * len(neg))


# ---------------------------------------------------------------------------
# Jev, cached
# ---------------------------------------------------------------------------
def question_hash():
    blob = json.dumps(jev_read.paragraph_questions(0), sort_keys=True) + json.dumps(
        jev_read.piece_questions(), sort_keys=True) + jev_read.__version__
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def jev_sweep(rows, docs, cache, qh, model_note):
    out = []
    for row, (path, meta) in zip(rows, docs):
        key = hashlib.sha256(row["t"].encode("utf-8")).hexdigest()[:16] + ":" + qh + ":" + register_of(meta)
        if key in cache:
            r = cache[key]
            r["cached"] = True
        else:
            t0 = time.time()
            r = jev_read.read(row["t"], genre=register_of(meta))
            r["seconds"] = round(time.time() - t0, 2)
            r["cached"] = False
            cache[key] = r
            model_note.add(r.get("model") or r["model_requested"])
        out.append({"file": row["file"], "jev": r})
    return out


def jev_metrics(entry):
    r = entry["jev"]
    if r.get("skipped"):
        return None
    m = {"texture": r["texture"]["score"]}
    for tell in jev_read.PARAGRAPH_TELLS:
        m[tell] = r["tells"][tell]["mean_p"]
    for tell in ("no_friction", "template", "callback"):
        m[tell] = r["tells"][tell]["p"]
    rh = r["rhythm"]
    # Low variation is the tell, so the metric is inverted to point the same way
    # as the others: higher = more machine-shaped.
    m["beat_uniformity"] = (1.0 - rh["sentences_per_paragraph_cv"]) if rh.get("sentences_per_paragraph_cv") is not None else None
    return m


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def fmt_delta(a, b, pct=False):
    d = b - a
    if pct:
        return f"{a:6.1%} -> {b:6.1%}  ({d:+.1%})"
    return f"{a:6.2f} -> {b:6.2f}  ({d:+.2f})"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", default=None, help="git ref holding the baseline checker (default main, then origin/main)")
    ap.add_argument("--human", default=str(ROOT / "tests" / "fp-corpus"), help="directory of known-human .md")
    ap.add_argument("--machine", default=str(ROOT / "tests" / "ai-corpus"), help="directory of machine-drafted .md")
    ap.add_argument("--limit", type=int, default=None, help="documents per class (for a cheap first run)")
    ap.add_argument("--jev", action="store_true", help="also run the Jev read on the branch (needs TYPESAFE_API_KEY)")
    ap.add_argument("--gate", action="store_true", help="exit 1 if the branch is worse than the baseline on rules")
    ap.add_argument("--json", metavar="PATH", default=None, help="where to write the full results (default evals/out/ab-<time>.json)")
    ap.add_argument("--no-cache", action="store_true", help="ignore and do not write the Jev cache")
    args = ap.parse_args(argv)

    base, ref, base_sha = load_baseline(args.baseline)
    human = load_corpus(args.human, "human", args.limit)
    machine = load_corpus(args.machine, "machine", args.limit)

    print(f"A/B  baseline {ref} ({base_sha}, humanist {getattr(base, '__version__', '?')}, {len(base.CHECKS)} rules)"
          f"  vs  branch HEAD ({head_sha()}, humanist {branch.__version__}, {len(branch.CHECKS)} rules)")
    print(f"     human   {len(human)} document(s) from {Path(args.human).relative_to(ROOT) if Path(args.human).is_relative_to(ROOT) else args.human}")
    print(f"     machine {len(machine)} document(s) from {Path(args.machine).relative_to(ROOT) if Path(args.machine).is_relative_to(ROOT) else args.machine}")
    print()

    results = {"baseline": {"ref": ref, "sha": base_sha}, "branch": {"sha": head_sha()}, "classes": {}}
    sweeps = {}
    for label, docs in (("human", human), ("machine", machine)):
        b_rows, h_rows = sweep(base, docs), sweep(branch, docs)
        sweeps[label] = (b_rows, h_rows)
        bd, hd = density(b_rows), density(h_rows)
        results["classes"][label] = {"baseline": bd, "branch": hd,
                                     "docs": [{k: v for k, v in r.items() if k != "t"} for r in h_rows]}
        print(f"RULES  {label} ({hd['docs']} docs, {hd['words']:,} words)          baseline -> branch")
        print(f"       FAIL per 1k      {fmt_delta(bd['fail_per_1k'], hd['fail_per_1k'])}")
        print(f"       WARN per 1k      {fmt_delta(bd['warn_per_1k'], hd['warn_per_1k'])}")
        print(f"       blocked          {fmt_delta(bd['blocked'], hd['blocked'], pct=True)}")
        changed = [(b, h) for b, h in zip(b_rows, h_rows) if (b["fails"], b["warns"]) != (h["fails"], h["warns"])]
        if changed:
            print(f"       {len(changed)} document(s) changed verdict or count:")
            for b, h in changed:
                gained = sorted(set(h["fail_rules"]) - set(b["fail_rules"]))
                lost = sorted(set(b["fail_rules"]) - set(h["fail_rules"]))
                print(f"         {h['file']:40} FAIL {b['fails']}->{h['fails']}  WARN {b['warns']}->{h['warns']}"
                      + (f"  +{gained}" if gained else "") + (f"  -{lost}" if lost else ""))
        else:
            print("       no document changed FAIL or WARN count")
        print()

    hb, hh = results["classes"]["human"]["baseline"], results["classes"]["human"]["branch"]
    mb, mh = results["classes"]["machine"]["baseline"], results["classes"]["machine"]["branch"]
    sep_b = mb["fail_per_1k"] - hb["fail_per_1k"]
    sep_h = mh["fail_per_1k"] - hh["fail_per_1k"]
    results["separation"] = {"baseline_fail_per_1k": sep_b, "branch_fail_per_1k": sep_h}
    print("SEPARATION (machine minus human)                    baseline -> branch")
    print(f"       FAIL per 1k      {fmt_delta(sep_b, sep_h)}")
    print(f"       WARN per 1k      {fmt_delta(mb['warn_per_1k'] - hb['warn_per_1k'], mh['warn_per_1k'] - hh['warn_per_1k'])}")
    print(f"       blocked          {fmt_delta(mb['blocked'] - hb['blocked'], mh['blocked'] - hh['blocked'], pct=True)}")
    print()

    worse = []
    if hh["fail_per_1k"] > hb["fail_per_1k"] + 1e-9:
        worse.append(f"human FAIL density rose {hb['fail_per_1k']:.3f} -> {hh['fail_per_1k']:.3f} per 1k")
    if sep_h < sep_b - 1e-9:
        worse.append(f"rules separation fell {sep_b:.3f} -> {sep_h:.3f} FAIL per 1k")

    if args.jev:
        OUT.mkdir(parents=True, exist_ok=True)
        cache_path = OUT / "jev-cache.json"
        cache = {}
        if not args.no_cache and cache_path.exists():
            try:
                cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cache = {}
        qh = question_hash()
        models = set()
        try:
            jev_read.api_key()
            per_class = {}
            for label in ("human", "machine"):
                _b_rows, h_rows = sweeps[label]
                docs = human if label == "human" else machine
                per_class[label] = jev_sweep(h_rows, docs, cache, qh, models)
        except jev_read.JevUnavailable as e:
            print(f"JEV    not run: {e}")
            print("       Set TYPESAFE_API_KEY and rerun with --jev. The rules comparison above stands on its own.")
            per_class = None
        finally:
            if not args.no_cache and cache:
                cache_path.write_text(json.dumps(cache), encoding="utf-8")

        if per_class:
            metrics = {label: [m for m in (jev_metrics(e) for e in entries) if m] for label, entries in per_class.items()}
            tokens = sum(e["jev"]["input_tokens"] for entries in per_class.values() for e in entries if not e["jev"].get("cached"))
            cached = sum(1 for entries in per_class.values() for e in entries if e["jev"].get("cached"))
            print(f"JEV    model {', '.join(sorted(models)) or 'cached only'}; {tokens:,} new input tokens; {cached} document(s) from cache")
            print(f"       questions hash {qh}")
            print(f"       {'metric':16} {'human mean':>11} {'machine mean':>13} {'AUC':>6}   (AUC: P(machine > human); 0.5 = coin)")
            results["jev"] = {"question_hash": qh, "metrics": {}}
            names = ["texture"] + list(jev_read.PARAGRAPH_TELLS) + ["no_friction", "template", "callback", "beat_uniformity"]
            for name in names:
                hv = [m[name] for m in metrics["human"] if m.get(name) is not None]
                mv = [m[name] for m in metrics["machine"] if m.get(name) is not None]
                a = auc(mv, hv)
                results["jev"]["metrics"][name] = {"human_mean": st.mean(hv) if hv else None,
                                                   "machine_mean": st.mean(mv) if mv else None, "auc": a,
                                                   "n_human": len(hv), "n_machine": len(mv)}
                print(f"       {name:16} {st.mean(hv) if hv else float('nan'):11.2f} {st.mean(mv) if mv else float('nan'):13.2f} "
                      f"{a if a is not None else float('nan'):6.2f}")
            results["jev"]["per_document"] = {label: [{"file": e["file"], **(jev_metrics(e) or {})} for e in entries]
                                              for label, entries in per_class.items()}
            print()
            print("       Read AUC with the n beside it. Six machine documents by one author resolve")
            print("       nothing finer than a coin versus a certainty. Bring a larger private corpus")
            print("       with --machine before quoting a number.")
            print()

    out_path = Path(args.json) if args.json else OUT / f"ab-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"written  {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}")

    if args.gate and worse:
        print("\nA/B GATE FAILED:", file=sys.stderr)
        for w in worse:
            print(f"  - {w}", file=sys.stderr)
        return 1
    if worse:
        print("\nnote: " + "; ".join(worse) + "  (pass --gate to make this fail the run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
