#!/usr/bin/env python3
"""Structure, manifest, reference and privacy validator for the humanist repo.

Dependency-free (stdlib only) so it runs anywhere, including CI without the Claude
Code CLI or Node. Seven gates:

  1. MANIFESTS   .claude-plugin/marketplace.json and plugins/humanist/.claude-plugin/
                 plugin.json parse and carry the fields the loader needs.
  2. SKILLS      every plugins/*/skills/<dir>/SKILL.md has YAML frontmatter whose
                 `name` matches <dir> and which declares a non-empty `description`.
  3. REFERENCES  every relative path named in a tracked markdown file exists on disk.
                 A doc that points at a file that is not there is a broken promise.
  4. PRIVACY     no absolute home paths, email addresses, local temp paths, key
                 material or tokens anywhere in the tree. This gate is the reason the
                 repo can be handed to anyone. Shipped patterns describe the SHAPE of
                 a leak, never anyone's identity; personal terms go in the gitignored
                 .privacy-terms. PRIVACY_ALLOW holds the deliberate exceptions.
  5. SPELLING    American English throughout. House style, mechanically enforced,
                 because a prose project that is inconsistent about its own spelling
                 has no business lecturing anyone. Vendored and public-domain text is
                 exempt: its spelling is not ours to change.
  6. GATE        the prose checker's own --selftest passes.
  7. APP         both Inkwash suites pass, when Node is available: the engine tests
                 and the document-import tests. Skipped with a printed notice when
                 Node is absent, never silently.

Exit 0 on success, 1 on any problem. Problems print with their file and line.

    python scripts/validate_repo.py
    python scripts/validate_repo.py --skip-slow      # gates 1-4 only
"""
# Makes every annotation in this file a lazy string, so PEP 604 syntax (`X | None`)
# cannot blow up at import time on the oldest Python the README claims to support.
# This landed after a `-> Path | None` return annotation failed CI on 3.9 with
# "unsupported operand type(s) for |". A grep would have found those two; this
# forecloses the whole class.
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []
notes: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# PRIVACY GATE
#
# STRUCTURAL patterns only. Every one describes the SHAPE of a leak rather than
# anyone's identity, which is what makes the list safe to commit.
#
# The design rule, because it is easy to get backwards: a denylist of secrets is a
# disclosure of secrets. Writing the usernames, handles and private project names
# you want caught INTO a tracked file produces a greppable inventory of exactly the
# things you were protecting, which is a stronger disclosure than most of what the
# patterns catch. So nothing identifying goes here, including in a comment.
#
# Personal terms belong in `.privacy-terms`, which is gitignored. See load_terms().
PRIVACY_PATTERNS = [
    (r"[A-Za-z]:[\\/]Users[\\/][A-Za-z0-9._-]+", "absolute Windows user path"),
    (r"/(?:home|Users)/[A-Za-z0-9._-]+/", "absolute POSIX home path"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email address"),
    (r"\bAppData[\\/]Local[\\/]Temp\b", "local temp path"),
    (r"\.claude[\\/]projects[\\/]", "local Claude session path"),
    (r"\b(?:ssh-rsa|ssh-ed25519|BEGIN [A-Z ]*PRIVATE KEY)\b", "private key material"),
    (r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{16,}", "GitHub token"),
    (r"\bsk-[A-Za-z0-9]{20,}", "API secret key"),
]

TERMS_FILE = ".privacy-terms"


def load_terms() -> list[str]:
    """Read personal terms from an untracked local file.

    One term per line, blank lines and # comments ignored. Matched
    case-insensitively on word boundaries. The file is gitignored on purpose:
    the whole point is that these strings never enter version control.

    Absent the file the structural patterns above still run, and the run says so
    out loud rather than reporting a clean sweep it did not perform.
    """
    p = ROOT / TERMS_FILE
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out

# Deliberate exceptions, each with the reason it is allowed.
PRIVACY_ALLOW = {
    # MIT requires a named copyright holder; this is an authorship statement, not
    # leaked personal data. Change the name here if the repo changes hands.
    "LICENSE": ["copyright holder"],
    "plugins/humanist/skills/humanist/third_party/humanizer/LICENSE": ["copyright holder"],
    # This validator necessarily contains the patterns it searches for.
    "scripts/validate_repo.py": ["the structural patterns themselves"],
}

# The false-positive corpus is published third-party documents (RFCs, public-domain
# books, government works). RFC 2119 carries its author's contact line, and that is
# the document's own content, not this project's leaked data. Redacting it would
# corrupt a regression fixture to satisfy a rule aimed at something else entirely.
PRIVACY_SKIP_PREFIXES = ("tests/fp-corpus/",)

SCAN_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".html", ".mjs", ".js",
                 ".txt", ".toml", ".cfg", ".sh", ".ps1"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def tracked_files() -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            out.append(Path(dirpath) / fn)
    return sorted(out)


def gate_privacy(files: list[Path]) -> None:
    compiled = [(re.compile(p, re.I), label) for p, label in PRIVACY_PATTERNS]
    terms = load_terms()
    if terms:
        compiled.append((re.compile(r"\b(?:" + "|".join(re.escape(x) for x in terms) + r")\b", re.I),
                         "local private term"))
    scanned = 0
    for path in files:
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        key = rel(path)
        if key.startswith(PRIVACY_SKIP_PREFIXES):
            continue
        allowed = PRIVACY_ALLOW.get(key)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        if allowed:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for rx, label in compiled:
                m = rx.search(line)
                if m:
                    err(f"PRIVACY {key}:{lineno}: {label} -> {m.group(0)!r}")
    if terms:
        notes.append(f"privacy: scanned {scanned} file(s) against "
                     f"{len(PRIVACY_PATTERNS)} structural pattern(s) + {len(terms)} local term(s)")
    else:
        notes.append(f"privacy: scanned {scanned} file(s) against "
                     f"{len(PRIVACY_PATTERNS)} structural pattern(s); no {TERMS_FILE} found, "
                     "so no personal terms were checked (this is a gap, not a pass)")


# ---------------------------------------------------------------------------
# SPELLING GATE
#
# House style is American English. This is enforced rather than requested because
# spelling drift is exactly the kind of thing that survives review forever once it
# lands, and because a project whose whole premise is mechanical enforcement of
# prose rules should submit to one.
#
# Exempt by design: the false-positive corpus (published 1854-2018, and its
# spelling is evidence, not style), and anything vendored from someone else.
# ---------------------------------------------------------------------------
BRITISH_SPELLINGS = [
    "sanitise", "sanitiser", "sanitised", "normalise", "normalised", "normalises",
    "normalising", "normalisation", "neutralise", "neutralised", "itemise", "itemised",
    "organise", "organised", "organisation", "generalise", "generalised", "recognise",
    "recognised", "summarise", "summarised", "categorise", "prioritise", "optimise",
    "optimised", "minimise", "maximise", "utilise", "emphasise", "standardise",
    "analyse", "analysed", "analysing",
    "modelling", "modelled", "travelled", "travelling", "labelled", "labelling",
    "cancelled", "signalled",
    "licence", "licences", "licencing", "catalogue", "catalogues",
    "behaviour", "behaviours", "behavioural", "colour", "colours", "coloured",
    "artefact", "artefacts", "honour", "honours", "honoured", "favour", "favours",
    "favoured", "labour", "neighbour", "rumour",
    "centre", "centres", "metre", "metres", "theatre",
    "defence", "offence", "pretence", "grey", "greys",
    "whilst", "amongst", "judgement", "acknowledgement",
    "fulfil", "skilful", "wilful", "marvellous", "programme", "aluminium",
]
SPELLING_SKIP = ("tests/fp-corpus/", "third_party/", "LICENSE")


def gate_spelling(files: list[Path]) -> None:
    rx = re.compile(r"\b(?:" + "|".join(sorted(BRITISH_SPELLINGS, key=len, reverse=True)) + r")\b", re.I)
    scanned = 0
    for path in files:
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        key = rel(path)
        if any(s in key for s in SPELLING_SKIP) or key == "scripts/validate_repo.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for lineno, line in enumerate(text.splitlines(), 1):
            m = rx.search(line)
            if m:
                err(f"SPELLING {key}:{lineno}: {m.group(0)!r} is British; house style is American English")
    notes.append(f"spelling: scanned {scanned} file(s) against "
                 f"{len(BRITISH_SPELLINGS)} British spelling(s)")


# ---------------------------------------------------------------------------
# MANIFESTS
# ---------------------------------------------------------------------------
def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"missing file: {rel(path)}")
    except json.JSONDecodeError as e:
        err(f"invalid JSON in {rel(path)}: {e}")
    return None


def gate_manifests() -> Path | None:
    mkt = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    plugin_root = None
    if mkt is not None:
        if not mkt.get("name"):
            err("marketplace.json: missing 'name'")
        if not (isinstance(mkt.get("owner"), dict) and mkt["owner"].get("name")):
            err("marketplace.json: missing 'owner.name'")
        plugins = mkt.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            err("marketplace.json: 'plugins' must be a non-empty array")
        else:
            for i, p in enumerate(plugins):
                if not p.get("name"):
                    err(f"marketplace.json: plugins[{i}] missing 'name'")
                src = p.get("source")
                if not src:
                    err(f"marketplace.json: plugins[{i}] missing 'source'")
                elif isinstance(src, str) and src.startswith("./"):
                    target = ROOT / src[2:]
                    if not target.is_dir():
                        err(f"marketplace.json: plugins[{i}] source '{src}' is not a directory")
                    else:
                        plugin_root = target
    if plugin_root is None:
        plugin_root = ROOT / "plugins" / "humanist"
    pj = load_json(plugin_root / ".claude-plugin" / "plugin.json")
    if pj is not None and not pj.get("name"):
        err("plugin.json: missing 'name'")
    return plugin_root


def frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return None
    fields, key = {}, None
    for line in m.group(1).splitlines():
        fm = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if fm:
            key = fm.group(1)
            fields[key] = fm.group(2).strip()
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def gate_skills(plugin_root: Path) -> None:
    skills_dir = plugin_root / "skills"
    if not skills_dir.is_dir():
        err(f"missing {rel(skills_dir)} directory")
        return
    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    if not skill_dirs:
        err(f"no skills found under {rel(skills_dir)}")
    for d in skill_dirs:
        sk = d / "SKILL.md"
        if not sk.exists():
            err(f"skills/{d.name}/: missing SKILL.md")
            continue
        fm = frontmatter(sk)
        if fm is None:
            err(f"skills/{d.name}/SKILL.md: missing YAML frontmatter")
            continue
        if fm.get("name") != d.name:
            err(f"skills/{d.name}/SKILL.md: frontmatter name "
                f"{fm.get('name')!r} != directory {d.name!r}")
        desc = fm.get("description", "")
        if not desc:
            err(f"skills/{d.name}/SKILL.md: missing 'description'")
        elif len(desc) < 40:
            err(f"skills/{d.name}/SKILL.md: 'description' is {len(desc)} chars; "
                "too short to route on")
    notes.append(f"skills: checked {len(skill_dirs)}")


# ---------------------------------------------------------------------------
# REFERENCE INTEGRITY
# ---------------------------------------------------------------------------
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Only backticked strings that look like PATHS (they contain a slash). A bare
# `humanist.py` in prose names a file, it does not point at one from this
# directory, and treating the two the same produced nothing but noise.
BACKTICK_PATH_RE = re.compile(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:py|md|json|html|mjs|yml|yaml|txt))`")
# GitHub resolves ../../ links against the repository web UI, not the file tree.
GH_WEB_ROUTE_RE = re.compile(r"^\.\./\.\./(security|issues|pulls|discussions|releases|wiki|actions|compare|tree|blob)\b")


def gate_references(files: list[Path]) -> None:
    checked = broken = skipped = 0
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        if "tests/fp-corpus" in rel(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            targets = set(LINK_RE.findall(line)) | set(BACKTICK_PATH_RE.findall(line))
            for t in targets:
                if t.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                if GH_WEB_ROUTE_RE.match(t):
                    skipped += 1
                    continue
                t = t.split("#", 1)[0].strip()
                if not t or "." not in Path(t).name:
                    # Extensionless targets are web routes, not files on disk.
                    skipped += 1
                    continue
                checked += 1
                cand = (path.parent / t).resolve()
                if not cand.exists() and not (ROOT / t).exists():
                    broken += 1
                    err(f"REFERENCE {rel(path)}:{lineno}: points at {t!r}, "
                        "which does not exist")
    notes.append(f"references: checked {checked} relative path(s), {broken} broken, "
                 f"{skipped} web route(s) skipped")


# ---------------------------------------------------------------------------
# BEHAVIORAL GATES
# ---------------------------------------------------------------------------
def gate_selftest(plugin_root: Path) -> None:
    checker = plugin_root / "skills" / "humanist" / "humanist.py"
    if not checker.exists():
        err(f"missing prose checker at {rel(checker)}")
        return
    proc = subprocess.run([sys.executable, str(checker), "--selftest"],
                          capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-6:]
        err("GATE humanist.py --selftest failed:\n      " + "\n      ".join(tail))
    else:
        notes.append("gate: humanist.py --selftest passed")


def gate_app() -> None:
    suites = [ROOT / "app" / "test-inkwash.mjs", ROOT / "app" / "test-docx.mjs"]
    missing = [s for s in suites if not s.exists()]
    for s in missing:
        err(f"missing app test suite at {rel(s)}")
    if missing:
        return
    node = shutil.which("node")
    if not node:
        notes.append("app: SKIPPED, node not on PATH (this is a skip, not a pass)")
        return
    for suite in suites:
        proc = subprocess.run([node, str(suite)], capture_output=True, text=True, cwd=str(ROOT))
        if proc.returncode != 0:
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-8:]
            err(f"APP {suite.name} failed:\n      " + "\n      ".join(tail))
        else:
            last = [l for l in proc.stdout.strip().splitlines() if l.strip()][-1]
            notes.append(f"app {suite.name}: {last.strip()}")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skip-slow", action="store_true",
                    help="run the static gates only; skip the selftest and app suite")
    args = ap.parse_args()

    files = tracked_files()
    plugin_root = gate_manifests()
    gate_skills(plugin_root)
    gate_references(files)
    gate_privacy(files)
    gate_spelling(files)
    if not args.skip_slow:
        gate_selftest(plugin_root)
        gate_app()

    for n in notes:
        print(f"  {n}")

    if errors:
        print(f"\nVALIDATION FAILED ({len(errors)} problem(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("\nOK: structure, manifests, references, privacy and behavior all valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
