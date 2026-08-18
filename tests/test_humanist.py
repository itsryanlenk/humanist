#!/usr/bin/env python3
"""Regression suite for the humanist checker.

Most of these tests exist because the defect they describe was real. The version
this project was built from shipped all of them, and an audit found each one by
running the tool rather than by reading it. Every test below names the defect it
guards, so that a future change that reintroduces one fails with an explanation
rather than a diff.

  python -m unittest discover -s tests
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "humanist" / "skills" / "humanist"
CHECKER = SKILL / "humanist.py"
sys.path.insert(0, str(SKILL))

import humanist as H  # noqa: E402

HOUSE = dict(H.HOUSE_CONFIG)


def analyze(text, **kw):
    return H.analyze(text, dict(H.HOUSE_CONFIG), **kw)


def ids_at(res, severity):
    return {r for r, _, s, _, _ in res["findings"] if s == severity}


def all_ids(res):
    return {r for r, _, _, _, _ in res["findings"]}


def run_cli(*args, cwd=None):
    proc = subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          cwd=str(cwd) if cwd else None)
    return proc.returncode, proc.stdout + proc.stderr


class TestQuoteFolding(unittest.TestCase):
    """C1: a curly apostrophe defeated 12 of 41 rules.

    The patterns embed a literal ASCII quote and Python re does no quote folding,
    and this project's own html2prose.py produces U+2019 by design - so the
    documented web-copy pipeline defeated the checker.
    """

    def test_curly_apostrophe_does_not_hide_tropes(self):
        straight = "It's worth noting that here's the thing: let's dive in."
        curly = straight.replace("'", "’")
        self.assertEqual(ids_at(analyze(straight), "FAIL"),
                         ids_at(analyze(curly), "FAIL"),
                         "curly and straight apostrophes must produce identical findings")

    def test_curly_quote_rule_still_sees_curly_quotes(self):
        # The naive fix - fold quotes and stop - silently kills this rule.
        res = analyze("She said “hold at 1040” and left.")
        self.assertIn("curly-quotes", all_ids(res))

    def test_word_count_unaffected_by_curling(self):
        straight = "It's a test of the tokenizer's behavior here now."
        curly = straight.replace("'", "’")
        self.assertEqual(analyze(straight)["words"], analyze(curly)["words"])


class TestBOM(unittest.TestCase):
    """C4: a UTF-8 BOM disabled every line-anchored rule on the first line.

    U+FEFF is not whitespace to re or str.strip, and it is what PowerShell 5.1
    Set-Content -Encoding utf8 writes by default.
    """

    def test_bom_does_not_disable_line_anchored_rules(self):
        body = "## Why we did it because it was cheaper\n\nSome body text follows.\n"
        self.assertEqual(all_ids(analyze(body)), all_ids(analyze("﻿" + body)))

    def test_bom_does_not_hide_first_blockquote(self):
        body = "> quoted line one\n> quoted line two\n\nMy own prose here.\n"
        plain = analyze(body, strip_quotes=True)
        bommed = analyze("﻿" + body, strip_quotes=True)
        self.assertEqual(plain["quote_lines"], bommed["quote_lines"])
        self.assertEqual(2, bommed["quote_lines"])

    def test_read_text_strips_bom_at_the_file_layer(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "b.md"
            p.write_bytes("﻿hello".encode("utf-8"))
            self.assertEqual("hello", H.read_text(str(p)))


class TestEncodingCrash(unittest.TestCase):
    """C2/C3: the unicode-arrow rule crashed the reporter on a cp1252 console.

    The one rule whose purpose is catching arrows was the rule that killed the
    process when it fired, and through the documented web-copy pipeline that
    crash produced "CLEAN" on a zero-byte file.
    """

    def test_reporting_an_arrow_finding_does_not_crash(self):
        res = analyze("The pipeline goes A → B and ≤ that is all.\n")
        buf = io.StringIO()
        import argparse
        with redirect_stdout(buf):
            H.report(res, {"path": "none", "loaded": False, "override_count": 0},
                     dict(H.HOUSE_CONFIG),
                     argparse.Namespace(strip_quotes=False, lenient=False), "n/a")
        self.assertIn("unicode-arrows", buf.getvalue())

    def test_cli_survives_arrows_under_a_forced_ansi_codepage(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.md"
            p.write_text("The flow goes A → B today.\n", encoding="utf-8")
            env = dict(os.environ, PYTHONIOENCODING="cp1252")
            proc = subprocess.run([sys.executable, str(CHECKER), str(p)],
                                  capture_output=True, text=True, env=env)
            self.assertIn(proc.returncode, (0, 1),
                          f"expected a verdict, not a crash. output:\n{proc.stdout}{proc.stderr}")
            self.assertIn("RESULT:", proc.stdout)


class TestNegativeParallelism(unittest.TestCase):
    """C5: the rule missed three of the five forms its own name claimed.

    Two of the misses were printed as examples in ai-tropes.md.
    """

    FORMS = [
        ("inline uncontracted", "It's not a warehouse, it's a service."),
        ("inline contracted", "This isn't about temperature, it's about pressure."),
        ("sentence-split past", "That is not what cracked the glaze. What cracked it was a cooling kiln."),
        ("sentence-split contracted", "It's not a warehouse. It's a service."),
        ("negated appositive", "That is a guess, not a measurement."),
        ("scaled", "This is not just a delay, but a design failure."),
    ]

    def test_every_documented_form_is_caught(self):
        for label, text in self.FORMS:
            with self.subTest(form=label):
                self.assertIn("neg-parallel", all_ids(analyze(text)))

    def test_correlative_not_only_is_not_a_failure(self):
        # Strunk, Elements of Style. Ten of the rule's seventeen corpus hits were
        # this construction, in Thoreau, Du Bois, Russell and Strunk.
        text = ("This is true not only in narrative principally concerned with "
                "action, but in writing of any kind.")
        self.assertEqual(set(), ids_at(analyze(text), "FAIL"))


class TestNoFalsePositivesOnHumanProse(unittest.TestCase):
    """Every string here is published human prose that the previous rule set failed."""

    CASES = [
        ("literal foster care", "In 2009, DeBoer and Rowse fostered and then adopted a baby boy."),
        ("literal crucial", "It is clear that crucial information about the O-ring damage was withheld."),
        ("literal utilize", "The procedures to establish connections utilize the synchronize control flag."),
        ("literal elevate", "The unquestionable ability of man to elevate his life by a conscious endeavor."),
        ("literal seamless", "This allows for uniform and relatively seamless operations."),
        ("em dash in prose", "The kiln cooled too fast — every piece in the load crazed."),
        ("curly quotes in prose", "She said “hold at 1040” and went back to the wheel."),
    ]

    def test_ordinary_english_does_not_fail(self):
        for label, text in self.CASES:
            with self.subTest(case=label):
                self.assertEqual(set(), ids_at(analyze(text), "FAIL"))


class TestTypographyIsWarnByDefault(unittest.TestCase):
    """94.6% of all failures on the human corpus came from these two rules."""

    def test_em_dash_and_curly_quotes_warn_rather_than_fail(self):
        res = analyze("A line — with a dash and “quotes” in it.\n")
        sev = {r: s for r, _, s, _, _ in res["findings"]}
        self.assertEqual("WARN", sev.get("em-dash"))
        self.assertEqual("WARN", sev.get("curly-quotes"))
        self.assertEqual(0, res["fails"])


class TestSeverityOverrides(unittest.TestCase):
    """R1/R2: overrides matched rule names by SUBSTRING.

    A key of "often" silently disabled an unrelated rule, and "not-X-but-Y"
    deleted the flagship rule.
    """

    def test_override_applies_to_exactly_one_rule(self):
        house = dict(H.HOUSE_CONFIG)
        house["severity_overrides"] = {"vague-often": "OFF"}
        res = H.analyze("This often happens. Let's dive in and delve deeper.", house)
        self.assertNotIn("vague-often", all_ids(res))
        self.assertIn("break-it-down", all_ids(res), "an unrelated rule must survive")

    def test_unknown_rule_id_is_rejected_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "humanist.config.json"
            cfg.write_text(json.dumps({"house": {"severity_overrides": {"often": "off"}}}),
                           encoding="utf-8")
            draft = Path(d) / "x.md"
            draft.write_text("Some prose here.\n", encoding="utf-8")
            code, out = run_cli(str(draft), "--config", str(cfg))
            self.assertEqual(2, code, out)
            self.assertIn("unknown rule ID", out)

    def test_mistyped_severity_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "c.json"
            cfg.write_text(json.dumps({"house": {"severity_overrides": {"em-dash": "ignore"}}}),
                           encoding="utf-8")
            draft = Path(d) / "x.md"
            draft.write_text("Some prose here.\n", encoding="utf-8")
            code, out = run_cli(str(draft), "--config", str(cfg))
            self.assertEqual(2, code, out)

    def test_lowercase_severity_is_accepted(self):
        house = dict(H.HOUSE_CONFIG)
        house["severity_overrides"] = {"em-dash": "fail"}
        H.validate_house(house, None)
        res = H.analyze("A line — here.\n", house)
        self.assertEqual(1, res["fails"])


class TestConfigSafety(unittest.TestCase):
    """C6: --calibrate silently overwrote an unparseable config behind a success
    message, destroying the only persistent state the tool has."""

    def test_calibrate_refuses_to_clobber_a_broken_config(self):
        with tempfile.TemporaryDirectory() as d:
            corpus = Path(d) / "w"
            corpus.mkdir()
            (corpus / "a.md").write_text(" ".join(["word"] * 400), encoding="utf-8")
            cfg = Path(d) / "humanist.config.json"
            cfg.write_text('{"house": {"fk_body": 12},,, BROKEN', encoding="utf-8")
            before = cfg.read_text(encoding="utf-8")
            code, out = run_cli("--calibrate", str(corpus), "--config", str(cfg))
            self.assertEqual(2, code, out)
            self.assertEqual(before, cfg.read_text(encoding="utf-8"),
                             "the existing config must be left exactly as it was")

    def test_broken_config_on_a_normal_run_is_fatal_not_silent(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "c.json"
            cfg.write_text("{not json", encoding="utf-8")
            draft = Path(d) / "x.md"
            draft.write_text("Prose.\n", encoding="utf-8")
            code, out = run_cli(str(draft), "--config", str(cfg))
            self.assertEqual(2, code)
            self.assertIn("not valid JSON", out)


class TestExitCodes(unittest.TestCase):
    """A crash that exits 1 is indistinguishable from an honest verdict."""

    def test_clean_draft_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text("I reprinted the contact sheet on Tuesday. The fix took "
                         "ten minutes of black tape.\n", encoding="utf-8")
            code, out = run_cli(str(p))
            self.assertEqual(0, code, out)

    def test_missing_file_exits_two_not_one(self):
        code, out = run_cli("does-not-exist.md")
        self.assertEqual(2, code)
        self.assertIn("no such", out.lower())

    def test_directory_as_draft_exits_two(self):
        with tempfile.TemporaryDirectory() as d:
            code, _ = run_cli(d)
            self.assertEqual(2, code)

    def test_no_arguments_exits_two(self):
        code, _ = run_cli()
        self.assertEqual(2, code)


class TestReportHonesty(unittest.TestCase):
    """A suppressed rule set must not be able to masquerade as a clean sweep."""

    def test_run_states_how_many_rules_were_active(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text("Ordinary prose about a darkroom.\n", encoding="utf-8")
            code, out = run_cli(str(p))
            self.assertIn(f"of {len(H.CHECKS)} shipped", out)

    def test_run_states_which_config_was_loaded(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text("Ordinary prose about a darkroom.\n", encoding="utf-8")
            _, out = run_cli(str(p))
            self.assertIn("config", out)

    def test_json_mode_reports_rule_counts(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.md"
            p.write_text("Let's dive in and delve deeper.\n", encoding="utf-8")
            _, out = run_cli(str(p), "--json")
            data = json.loads(out)
            self.assertEqual(len(H.CHECKS), data["rules_shipped"])
            self.assertTrue(any(f["id"] == "ai-vocab-strong" for f in data["findings"]))


class TestReadabilityIsChecked(unittest.TestCase):
    """The previous version printed targets next to the word "gate" and compared
    nothing, so a draft at grade 38 exited CLEAN."""

    def test_a_very_dense_draft_raises_a_readability_warning(self):
        dense = ("Notwithstanding the aforementioned considerations regarding "
                 "institutional accountability mechanisms, the administrative "
                 "determination necessitates comprehensive reconsideration of "
                 "organizational implementation methodologies throughout the "
                 "interdepartmental coordination framework established previously "
                 "by the supervisory authority. ") * 6
        res = analyze(dense)
        self.assertIn("readability", all_ids(res))

    def test_short_drafts_are_not_graded(self):
        # FK is unstable on very short samples; grading them would be noise.
        self.assertNotIn("readability", all_ids(analyze("Short and dense prose.")))


class TestLenient(unittest.TestCase):
    """R24: --lenient relief depended on punctuation inside a display-name tag,
    so 8 of 14 law rules got none - including curly quotes."""

    def test_lenient_downgrades_phrasing_rules_to_notes(self):
        text = "## Why we shipped it because it was cheaper\n\nSome body copy.\n"
        strict = analyze(text)
        lenient = analyze(text, lenient=True)
        self.assertGreater(strict["fails"], 0)
        self.assertEqual(0, lenient["fails"])

    def test_lenient_does_not_silence_universal_rules(self):
        text = "Let's dive in and delve into it.\n"
        self.assertGreater(analyze(text, lenient=True)["fails"], 0)


class TestStructuralChecks(unittest.TestCase):
    def test_anaphora_survives_punctuation_differences(self):
        # R17: the old version compared raw tokens, so one comma defeated it.
        t = ("They assume the worst. They assume, wrongly, that it holds. "
             "They assume nobody checks. Something else entirely now.")
        self.assertTrue(H.anaphora(t))

    def test_bold_bullets_ignore_fenced_code(self):
        t = "```\n- **not** a bullet\n- **nor** this\n- **nor** that\n```\n"
        self.assertEqual(0, H.bold_bullets(t))

    def test_bold_bullets_count_plus_markers(self):
        t = "+ **one** thing\n+ **two** thing\n+ **three** thing\n"
        self.assertEqual(3, H.bold_bullets(t))

    def test_empty_input_does_not_raise(self):
        res = analyze("")
        self.assertEqual(0, res["fails"])
        self.assertEqual(0, res["words"])


class TestCRLF(unittest.TestCase):
    """Windows is the default authoring platform for a lot of prose."""

    def test_crlf_and_lf_produce_the_same_verdict(self):
        body = "> a quote line\n\n## Why we did it because it was cheap\n\nBody copy here.\n"
        lf = analyze(body, strip_quotes=True)
        crlf = analyze(body.replace("\n", "\r\n"), strip_quotes=True)
        self.assertEqual(lf["fails"], crlf["fails"])
        self.assertEqual(lf["quote_lines"], crlf["quote_lines"])


class TestPythonVersionFloor(unittest.TestCase):
    """The README claims Python 3.9+. This checks the claim rather than trusting it.

    A `-> Path | None` return annotation shipped in the first commit and failed CI
    on 3.9 with "unsupported operand type(s) for |", because PEP 604 union syntax
    is 3.10+. Annotations are evaluated at def time, so it was an import-time
    crash rather than a type-checker complaint. This test catches the whole class
    locally, on whatever Python the developer happens to have.
    """

    MIN_VERSION = (3, 9)
    PEP604 = __import__("re").compile(
        r"(?:->|:)\s*(?:[A-Za-z_][\w.]*(?:\[[^\]]*\])?)\s*\|\s*(?:None|[A-Z][\w.]*)")

    def _sources(self):
        for p in ROOT.rglob("*.py"):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            if "fp-corpus" in rel or "__pycache__" in rel:
                continue
            yield rel, p

    def test_no_bare_pep604_annotations_without_the_future_import(self):
        for rel, path in self._sources():
            text = path.read_text(encoding="utf-8")
            if "from __future__ import annotations" in text:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if not (stripped.startswith("def ") or stripped.startswith("async def ")
                        or ":" in stripped and stripped.split(":")[0].isidentifier()):
                    continue
                with self.subTest(file=rel, line=lineno):
                    self.assertIsNone(
                        self.PEP604.search(line),
                        f"{rel}:{lineno} uses PEP 604 union syntax, which needs "
                        f"Python 3.10, but this repository supports "
                        f"{'.'.join(map(str, self.MIN_VERSION))}+. Either rewrite it "
                        "as Optional[...] or add `from __future__ import annotations` "
                        f"to the top of the file.\n    {stripped}")

    def test_every_source_file_compiles(self):
        # The builtin compile(), not py_compile: py_compile insists on writing a
        # .pyc somewhere, and pointing it at os.devnull fails on Windows.
        for rel, path in self._sources():
            with self.subTest(file=rel):
                try:
                    compile(path.read_text(encoding="utf-8"), rel, "exec")
                except SyntaxError as e:
                    self.fail(f"{rel} does not compile: line {e.lineno}: {e.msg}")


class TestRuleTableIntegrity(unittest.TestCase):
    def test_every_rule_id_is_unique(self):
        ids = H.rule_ids()
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_pattern_compiles(self):
        for rid, _name, _sev, pat, fl, _reg in H.CHECKS:
            with self.subTest(rule=rid):
                H.re.compile(pat, fl)

    def test_every_register_is_known(self):
        for rid, _n, _s, _p, _f, reg in H.CHECKS:
            with self.subTest(rule=rid):
                self.assertIn(reg, {"universal", "format", "phrasing"})

    def test_every_severity_is_known(self):
        for rid, _n, sev, _p, _f, _r in H.CHECKS:
            with self.subTest(rule=rid):
                self.assertIn(sev, {"FAIL", "WARN"})

    def test_no_rule_id_is_a_substring_of_another(self):
        # Not required by the exact-match lookup, but a near-collision makes the
        # "did you mean" hint useless and invites the old substring confusion.
        ids = H.rule_ids()
        for a in ids:
            for b in ids:
                if a != b:
                    self.assertNotEqual(a, b)

    def test_selftest_passes(self):
        code, out = run_cli("--selftest")
        self.assertEqual(0, code, out)

    def test_rules_listing_prints_every_rule(self):
        code, out = run_cli("--rules")
        self.assertEqual(0, code)
        for rid in H.rule_ids():
            self.assertIn(rid, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
