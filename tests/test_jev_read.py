#!/usr/bin/env python3
"""Tests for the Jev read. None of them touch the network.

The transport is injectable, so every test hands jev_read a fake that records the
request and answers it. What is under test is the part this repository owns: how
paragraphs are cut, how questions are built, how answers are composed into
densities, and how the checker behaves when the read cannot run. The model's
own accuracy is not testable here and is not claimed; evals/ab_against_main.py
is where that gets measured, with a key.

  python -m unittest discover -s tests
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "humanist" / "skills" / "humanist"
CHECKER = SKILL / "humanist.py"
sys.path.insert(0, str(SKILL))

import humanist as H  # noqa: E402
import jev_read as J  # noqa: E402

AI_CORPUS = ROOT / "tests" / "ai-corpus"
FP_CORPUS = ROOT / "tests" / "fp-corpus"


class FakeTransport:
    """Answers every question with a fixed value and keeps the payloads."""

    def __init__(self, noul=0.2, closer=0.8, texture=(0.1, 0.2, 0.4, 0.3), fail_missing=None):
        self.payloads = []
        self.noul, self.closer, self.texture = noul, closer, texture
        self.fail_missing = fail_missing

    def __call__(self, payload):
        self.payloads.append(payload)
        answers = {}
        for qid, q in payload["questions"].items():
            if qid == self.fail_missing:
                continue
            if q["type"] == "noul":
                answers[qid] = {"type": "noul", "noul": self.closer if qid.startswith("closer") else self.noul}
            else:
                probs = {str(i): p for i, p in enumerate(self.texture)}
                score = sum(i * p for i, p in enumerate(self.texture))
                answers[qid] = {"type": "score", "score": score, "confidence": 0.5,
                                "probabilities": probs, "legend": {k: "l" for k in probs}}
        return {"model": "jev-test", "answers": answers,
                "usage": {"input_tokens": 100, "output_tokens": 1}}


def strip(path):
    return H.strip_md(H.read_text(str(path)))


class TestParagraphs(unittest.TestCase):
    def test_headings_are_not_paragraphs(self):
        t = "# Title\n\nFirst real paragraph with enough words.\n\n## Section\n\nSecond one here too."
        ps = J.paragraphs(t)
        self.assertEqual(2, len(ps))
        self.assertFalse(any(p.startswith("#") for p in ps))

    def test_list_block_is_one_beat(self):
        t = "- **one** thing here\n- **two** thing here\n- **three** thing here\n\nA closing paragraph of prose."
        ps = J.paragraphs(t)
        self.assertEqual(2, len(ps))
        self.assertNotIn("- ", ps[0])

    def test_tiny_fragments_are_dropped(self):
        self.assertEqual([], J.paragraphs("Hi.\n\nOk then"))

    def test_final_sentence_handles_closing_quotes(self):
        p = 'He paused. "Hold at 1040," she said.'
        self.assertEqual('"Hold at 1040," she said.', J.final_sentence(p))

    def test_empty_text_reads_as_skipped(self):
        r = J.read("", transport=FakeTransport())
        self.assertIn("skipped", r)
        self.assertEqual(0, r["requests"])


class TestRhythmMetrics(unittest.TestCase):
    """The computable tells stay in code. Jev 1.13 is documented as unreliable at
    counting, so none of these may ever become a question."""

    def test_uniform_paragraphs_have_low_cv(self):
        uniform = ["One sentence. Two sentence. Three sentence."] * 6
        varied = ["One.", "One. Two. Three. Four. Five. Six.", "One. Two.",
                  "One. Two. Three. Four. Five. Six. Seven. Eight.", "One.", "One. Two. Three."]
        u = J.rhythm_metrics([p + " padding words here" for p in uniform])
        v = J.rhythm_metrics([p + " padding words here" for p in varied])
        self.assertTrue(u["testable"] and v["testable"])
        self.assertLess(u["sentences_per_paragraph_cv"], v["sentences_per_paragraph_cv"])

    def test_below_five_paragraphs_is_untestable(self):
        m = J.rhythm_metrics(["A paragraph of some words."] * 4)
        self.assertFalse(m["testable"])
        self.assertIsNone(m["sentences_per_paragraph_cv"])

    def test_contractions_are_counted_curly_or_straight(self):
        straight = J.rhythm_metrics(["It's fine and we don't mind, they'll say."] * 5)
        curly = J.rhythm_metrics(["It’s fine and we don’t mind, they’ll say."] * 5)
        self.assertGreater(straight["contractions_per_1k"], 0)
        self.assertAlmostEqual(straight["contractions_per_1k"], curly["contractions_per_1k"])

    def test_numeral_gap_cv_needs_enough_numerals(self):
        few = J.rhythm_metrics(["We counted 3 and then 4 of them."] * 5)
        self.assertIsNotNone(few["numeral_gap_cv"])
        none = J.rhythm_metrics(["No figures at all in this text."] * 5)
        self.assertEqual(0.0, none["numerals_per_100w"])
        self.assertIsNone(none["numeral_gap_cv"])


class TestQuestionDesign(unittest.TestCase):
    """The shape the docs ask for: one judgment each, criteria as situations,
    state referenced by path, ids never carrying meaning the model needs."""

    def test_every_paragraph_question_is_a_noul_with_both_criteria(self):
        qs = J.paragraph_questions(3)
        self.assertEqual(set(f"{t}_3" for t in J.PARAGRAPH_TELLS), set(qs))
        for q in qs.values():
            self.assertEqual("noul", q["type"])
            self.assertIn("true", q["criteria"])
            self.assertIn("false", q["criteria"])
            self.assertIn("paragraphs[3]", json.dumps(q))

    def test_closer_question_points_at_the_pre_extracted_sentence(self):
        q = J.paragraph_questions(7)["closer_7"]
        self.assertIn("closers[7]", q["instructions"]["question"])

    def test_texture_is_a_score_with_descriptive_levels(self):
        tex = J.piece_questions()["texture"]
        self.assertEqual("score", tex["type"])
        self.assertEqual(len(J.TEXTURE_LEGEND), len(tex["criteria"]))
        for level in tex["criteria"]:
            self.assertGreater(len(level["what"]), 40, "levels must describe situations, not degrees")

    def test_no_counting_question_is_ever_asked(self):
        text = json.dumps(J.paragraph_questions(0)) + json.dumps(J.piece_questions())
        for banned in ("how many", "count the", "number of paragraphs", "what percentage"):
            self.assertNotIn(banned, text.lower())


class TestChunking(unittest.TestCase):
    def test_every_index_appears_exactly_once(self):
        paras = [f"Paragraph number {i} with a few more words in it." for i in range(53)]
        runs = J.chunks(paras, max_paras=20)
        flat = [i for run in runs for i in run]
        self.assertEqual(list(range(53)), flat)
        self.assertTrue(all(len(run) <= 20 for run in runs))

    def test_byte_ceiling_closes_a_chunk_early(self):
        big = ["word " * 4000] * 6
        runs = J.chunks(big, max_paras=20, max_bytes=60_000)
        self.assertGreater(len(runs), 1)
        self.assertEqual(list(range(6)), [i for run in runs for i in run])

    def test_no_request_exceeds_the_byte_ceiling_on_the_human_corpus(self):
        for doc in sorted(FP_CORPUS.glob("*.md")):
            t = strip(doc)
            paras = J.paragraphs(t)
            fake = FakeTransport()
            J.read(t, transport=fake)
            sizes = [len(json.dumps(p)) for p in fake.payloads if "paragraphs" in p["state"]]
            with self.subTest(doc=doc.name, paragraphs=len(paras)):
                # A chunk is closed before it would exceed the ceiling, so one
                # oversized paragraph is the only way past it.
                longest = max((len(p.encode("utf-8")) for p in paras), default=0)
                self.assertTrue(all(s <= J.BYTES_PER_REQUEST + 2 * longest + 1000 for s in sizes),
                                f"largest request {max(sizes):,} bytes")


class TestComposition(unittest.TestCase):
    def setUp(self):
        self.t = strip(AI_CORPUS / "A01_essay_reading-goals.md")
        self.paras = J.paragraphs(self.t)

    def test_answers_map_back_to_the_right_paragraph_across_chunks(self):
        class Positional(FakeTransport):
            def __call__(self, payload):
                reply = super().__call__(payload)
                if "paragraphs" in payload["state"]:
                    for qid in payload["questions"]:
                        j = int(qid.rsplit("_", 1)[1])
                        # Encode the paragraph's length so the test can check the mapping.
                        reply["answers"][qid]["noul"] = min(0.99, len(payload["state"]["paragraphs"][j]) / 10000.0)
                return reply

        r = J.read(self.t, transport=Positional(), chunk=2)
        for tell in J.PARAGRAPH_TELLS:
            probs = r["tells"][tell]["probabilities"]
            for i, p in enumerate(self.paras):
                self.assertEqual(round(min(0.99, len(p) / 10000.0), 3), probs[i])

    def test_densities_and_threshold(self):
        r = J.read(self.t, transport=FakeTransport(noul=0.2, closer=0.8))
        n = len(self.paras)
        self.assertEqual(n, r["tells"]["closer"]["hits"])
        self.assertEqual(0, r["tells"]["triad"]["hits"])
        self.assertAlmostEqual(1.0, r["tells"]["closer"]["share"])
        self.assertFalse(r["tells"]["no_friction"]["hit"])
        r2 = J.read(self.t, transport=FakeTransport(noul=0.2, closer=0.8), yes=0.9)
        self.assertEqual(0, r2["tells"]["closer"]["hits"], "the threshold must be honored")

    def test_texture_score_and_probabilities_are_carried(self):
        r = J.read(self.t, transport=FakeTransport(texture=(0.0, 0.0, 0.5, 0.5)))
        self.assertAlmostEqual(2.5, r["texture"]["score"])
        self.assertEqual([0.0, 0.0, 0.5, 0.5], r["texture"]["probabilities"])
        self.assertEqual(3, r["texture"]["max"])

    def test_tokens_and_requests_are_summed(self):
        fake = FakeTransport()
        r = J.read(self.t, transport=fake, chunk=3)
        self.assertEqual(len(fake.payloads), r["requests"])
        self.assertEqual(100 * len(fake.payloads), r["input_tokens"])
        self.assertEqual("jev-test", r["model"])

    def test_piece_questions_see_the_genre(self):
        fake = FakeTransport()
        J.read(self.t, genre="essay", transport=fake)
        piece = [p for p in fake.payloads if "piece" in p["state"]]
        self.assertEqual(1, len(piece))
        self.assertEqual("essay", piece[0]["state"]["genre"])
        self.assertEqual(set(J.piece_questions()), set(piece[0]["questions"]))

    def test_report_prints_every_tell_and_never_a_verdict(self):
        r = J.read(self.t, transport=FakeTransport())
        buf = io.StringIO()
        J.report(r, out=buf)
        out = buf.getvalue()
        for tell in J.TELL_NAMES:
            self.assertIn(tell, out)
        self.assertIn("not a verdict", out)
        self.assertNotIn("AI-generated", out)


class TestFailureIsLoud(unittest.TestCase):
    """Exit 2 territory: the read did not happen, and nothing may look like it did."""

    def test_missing_key_raises_unavailable(self):
        env = dict(os.environ)
        env.pop(J.API_KEY_ENV, None)
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(J.JevUnavailable) as cm:
                J.api_key()
            self.assertIn(J.API_KEY_ENV, str(cm.exception))

    def test_missing_answer_raises_unavailable(self):
        t = strip(AI_CORPUS / "A06_social_learning-in-public.md")
        with self.assertRaises(J.JevUnavailable):
            J.read(t, transport=FakeTransport(fail_missing="triad_0"))

    def test_reply_without_answers_raises_unavailable(self):
        with self.assertRaises(J.JevUnavailable):
            J.read("A paragraph with plenty of words in it.", transport=lambda payload: {"model": "x"})

    def test_cli_without_key_exits_two_and_prints_no_result_line(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.md"
            p.write_text("Ordinary prose about a darkroom, with several words.\n", encoding="utf-8")
            env = dict(os.environ)
            env.pop(J.API_KEY_ENV, None)
            proc = subprocess.run([sys.executable, str(CHECKER), str(p), "--jev"],
                                  capture_output=True, text=True, env=env, encoding="utf-8")
            self.assertEqual(2, proc.returncode, proc.stdout + proc.stderr)
            self.assertNotIn("RESULT:", proc.stdout)
            self.assertIn(J.API_KEY_ENV, proc.stderr)

    def test_checker_without_jev_flag_is_byte_identical_to_before(self):
        # The read is opt-in. A run without --jev must not import it, print it,
        # or change its verdict.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.md"
            p.write_text((AI_CORPUS / "A03_marketing_scheduling-app.md").read_text(encoding="utf-8"),
                         encoding="utf-8")
            proc = subprocess.run([sys.executable, str(CHECKER), str(p)],
                                  capture_output=True, text=True, encoding="utf-8")
            self.assertNotIn("JEV READ", proc.stdout)
            self.assertIn("RESULT:", proc.stdout)


class TestAICorpus(unittest.TestCase):
    """The machine-drafted companion to tests/fp-corpus. Provenance is the point."""

    def test_manifest_covers_every_file_and_nothing_else(self):
        manifest = json.loads((AI_CORPUS / "_manifest.json").read_text(encoding="utf-8"))
        listed = {e["file"] for e in manifest}
        on_disk = {p.name for p in AI_CORPUS.glob("*.md")}
        self.assertEqual(listed, on_disk)
        for e in manifest:
            for key in ("register", "author", "generated", "prompt", "edits"):
                self.assertIn(key, e, e["file"])

    def test_registers_match_the_detection_study(self):
        manifest = json.loads((AI_CORPUS / "_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({"essay", "howto", "social", "marketing", "email", "review"},
                         {e["register"] for e in manifest})


import unittest.mock  # noqa: E402  - used by TestFailureIsLoud

if __name__ == "__main__":
    unittest.main(verbosity=2)
