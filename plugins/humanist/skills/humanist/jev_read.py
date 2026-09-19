#!/usr/bin/env python3
"""
jev_read.py - the rhythm tells as typed judgments, by way of TypeSafe's Jev.

  python humanist.py draft.md --jev [--genre essay]
  python jev_read.py draft.md [--genre essay] [--json]

WHY THIS FILE EXISTS. The detection study behind this repository found that the
tells surviving a clean checker run are all rhythmic and structural rather than
lexical: uniform beat rate, the aphoristic closer, tricolons, the announced
thesis, a piece with no friction. ai-tropes.md files them under "manual forever",
because no regular expression catches them without lying about its precision.

A regular expression is not the only mechanical instrument. Jev is a System One
model: it returns a calibrated probability for a yes/no question about a piece of
text, and nothing else. That is the right shape for "is this final sentence an
aphorism?", which is a judgment a regex cannot make and a person makes in a
second. So this module asks that question, once per paragraph, and lets code do
what code is good at: splitting the paragraphs, pulling the final sentence,
counting the hits, computing the variance.

WHAT IT IS NOT. It does not decide whether a machine wrote the text, it does not
edit, and it does not change the checker's exit code. It reports densities and a
texture score, and a person decides. Nothing here has been measured against a
commercial detector; the harness in evals/ab_against_main.py exists to measure it
against the two corpora this repository already holds.

DIVISION OF LABOR, following the model's documented jagged edges:
  - Counting, variance and arithmetic stay in code. Jev 1.13 does not count
    reliably, so the uniform-beat-rate metric is a coefficient of variation
    computed here, never a question.
  - One narrow judgment per question, criteria written as situations, state cut
    to the paragraph the question is about. A paragraph question names its
    paragraph by path (`paragraphs[3]`) and the final sentence is pre-extracted
    into `closers[3]` so the model is not asked to find it.
  - Requests are chunked so a long chapter does not push one request past the
    documented context budget.

CONFIGURATION. TYPESAFE_API_KEY is required. TYPESAFE_BASE_URL and
TYPESAFE_DEFAULT_MODEL are honored, matching the official SDK's variable names.
No SDK is imported: this repository is standard-library only and the HTTP API is
one POST.

Exit codes when run standalone: 0 the read ran, 2 it could not (no key, network,
malformed reply). There is no exit 1, because a density is not a verdict.
"""
import argparse
import json
import math
import os
import re
import statistics as st
import sys
import time
import urllib.error
import urllib.request

__version__ = "0.1.0"

API_KEY_ENV = "TYPESAFE_API_KEY"
BASE_URL_ENV = "TYPESAFE_BASE_URL"
MODEL_ENV = "TYPESAFE_DEFAULT_MODEL"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"
ENDPOINT = "/v1/systemone"

# Paragraphs per request, and a byte ceiling per request. The four paragraph
# questions repeat their criteria for every paragraph, about 5.5 KB a paragraph,
# so a chunk is closed when either bound is reached. 120 KB is roughly 30k
# tokens, half the 64k request budget the model page documents.
PARAGRAPHS_PER_REQUEST = 20
BYTES_PER_REQUEST = 120_000
# A Noul is the probability the answer is yes. This is the threshold at which a
# paragraph counts as a hit for the density figures. Reported alongside the mean
# probability so a reader can see how much the threshold is doing.
YES = 0.5
# Below this many paragraphs a coefficient of variation is noise, so the rhythm
# metrics print UNTESTABLE rather than a number. Same sampling law as the marker
# bands in humanist.py.
MIN_PARAGRAPHS_FOR_RHYTHM = 5
# Whole-piece questions see the piece once. Past this many words the piece is
# truncated for those questions only, and the report says so.
MAX_PIECE_WORDS = 12000

REQUEST_TIMEOUT = 30.0
RETRY_STATUSES = (429, 529)
RETRY_BACKOFF = (1.0, 2.0, 4.0)


class JevUnavailable(Exception):
    """The read could not run. Never a verdict about the prose."""


# ---------------------------------------------------------------------------
# Text handling. Everything here is code, deliberately.
# ---------------------------------------------------------------------------
_SENT_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]*\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
_CONTRACTION = re.compile(r"\b[A-Za-z]+['’](?:t|s|re|ve|ll|d|m)\b", re.I)
_NUMERAL = re.compile(r"(?<![A-Za-z])[$€£]?\d[\d,]*(?:\.\d+)?%?")
_LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def paragraphs(t):
    """Prose paragraphs from checker-ready text (the output of humanist.strip_md).

    Headings are dropped: they are structure, not beats. List items inside one
    block are joined into one paragraph, because a list is one beat however many
    lines it occupies. Blocks under three words are dropped as noise.
    """
    out = []
    for block in re.split(r"\n\s*\n", t):
        lines = []
        for line in block.split("\n"):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            lines.append(_LIST_MARKER.sub("", s))
        p = re.sub(r"\s+", " ", " ".join(lines)).strip()
        if len(_WORD.findall(p)) >= 3:
            out.append(p)
    return out


def sentences(p):
    return [s.strip() for s in _SENT_SPLIT.split(p) if s.strip()]


def final_sentence(p):
    s = sentences(p)
    return s[-1] if s else p


def _cv(values):
    if len(values) < 2:
        return None
    mean = st.mean(values)
    if mean == 0:
        return None
    return st.pstdev(values) / mean


def rhythm_metrics(paras):
    """The computable half of the rhythm tells. No model is involved.

    uniform beat rate -> coefficient of variation of sentences per paragraph
                         (and of words per paragraph). Low variation is the tell.
    contraction rate  -> contractions per 1,000 words. The study found
                         contraction *uniformity* to be a tell, and a rate of
                         exactly zero in a first-person register is the extreme.
    numbers as texture-> numerals per 100 words and the CV of the gaps between
                         them. Evenly sprinkled numbers are the tell; clustered
                         numbers are what evidence looks like.
    """
    joined = " ".join(paras)
    words = _WORD.findall(joined)
    nwords = len(words)
    sent_counts = [len(sentences(p)) for p in paras]
    word_counts = [len(_WORD.findall(p)) for p in paras]
    testable = len(paras) >= MIN_PARAGRAPHS_FOR_RHYTHM
    out = {
        "paragraphs": len(paras),
        "words": nwords,
        "testable": testable,
        "sentences_per_paragraph_cv": _cv(sent_counts) if testable else None,
        "words_per_paragraph_cv": _cv(word_counts) if testable else None,
        "contractions_per_1k": (len(_CONTRACTION.findall(joined)) * 1000.0 / nwords) if nwords else 0.0,
    }
    # Numeral positions in word index, so gaps are in words.
    positions, idx = [], 0
    for tok in re.findall(r"\S+", joined):
        if _NUMERAL.search(tok):
            positions.append(idx)
        idx += 1
    out["numerals_per_100w"] = (len(positions) * 100.0 / nwords) if nwords else 0.0
    gaps = [b - a for a, b in zip(positions, positions[1:])]
    out["numeral_gap_cv"] = _cv(gaps) if len(gaps) >= 3 else None
    return out


# ---------------------------------------------------------------------------
# Questions. One judgment each, criteria as situations, paths into the state.
# The ids are for code; the model never sees them, so every question carries
# its full meaning in its own text.
# ---------------------------------------------------------------------------
def _noul(question, inspect, true, false, focus=None):
    instr = {"question": question, "inspect": inspect}
    if focus:
        instr["focus"] = focus
    return {"type": "noul", "instructions": instr, "criteria": {"true": true, "false": false}}


PARAGRAPH_TELLS = ("closer", "triad", "thesis", "symmetry")

# Human-readable names and the ai-tropes.md entry each one implements.
TELL_NAMES = {
    "closer": "aphoristic closer: paragraph ends on a general, quotable line",
    "triad": "tricolon / announced triad inside the paragraph",
    "thesis": "announced thesis: a sentence stating the point instead of supplying material",
    "symmetry": "balanced clause symmetry or chiasmus",
    "no_friction": "too complete, no friction: every problem raised is also solved",
    "template": "genre-template completion: every slot filled once, in order",
    "callback": "planted-detail callback: an early detail recalled at the close",
}


def paragraph_questions(local_index):
    i = local_index
    p = "`paragraphs[%d]`" % i
    c = "`closers[%d]`" % i
    return {
        "closer_%d" % i: _noul(
            "Is %s an aphoristic closer?" % c,
            "%s, which is the last sentence of %s" % (c, p),
            true={
                "what": "A short general statement, quotable on its own, that resolves the "
                        "paragraph. It names no particular person, place, number or event, "
                        "and it could close many different paragraphs.",
                "examples": [
                    "Reading isn't a productivity metric, and treating it like one turned a pleasure into a chore.",
                    "The tool was never the problem.",
                    "Good habits are quiet.",
                ],
            },
            false={
                "what": "The sentence reports a particular: a named thing, a number, an event, "
                        "a next step, a question, or a thread left open. A paragraph that "
                        "simply stops mid-thought also counts as no.",
                "examples": [
                    "My colleague repeated the timing on Friday and got 10.",
                    "I never found out why the second batch failed.",
                    "The fix took ten minutes of black tape.",
                ],
            },
            focus="Judge the sentence's function, not its quality. A well-written particular is still no.",
        ),
        "triad_%d" % i: _noul(
            "Does %s contain a rhetorical triad?" % p,
            p,
            true={
                "what": "Three parallel items, clauses or sentences arranged for effect; or an "
                        "enumeration announced as exactly three; or a sentence built as "
                        "'A, B, and C' where the three share grammatical shape and none "
                        "carries specific content the others lack.",
                "examples": [
                    "It was faster, cleaner, and cheaper.",
                    "Setup, turn, payoff.",
                    "Three findings stood out.",
                ],
            },
            false={
                "what": "No grouping of three; or a list of three concrete named things that "
                        "happen to number three, such as three named people or three "
                        "ingredients.",
                "examples": [
                    "We invited Ana, Luis and the neighbor from 4B.",
                    "The kiln, the shelf and the box of cones were all still wet.",
                ],
            },
        ),
        "thesis_%d" % i: _noul(
            "Does %s contain a sentence that announces the piece's own thesis or point?" % p,
            p,
            true={
                "what": "A sentence that tells the reader what the piece is arguing or what to "
                        "take from it, instead of supplying material: 'the point is', 'what "
                        "this gets at', 'I keep coming back to', or a positioning line whose "
                        "two halves mirror each other.",
                "examples": [
                    "The real lesson is that speed was never the constraint.",
                    "Instead of the team adapting to the software, the software adapts to the team.",
                    "I keep coming back to the same conclusion.",
                ],
            },
            false={
                "what": "Every sentence supplies material: an event, a measurement, a step, a "
                        "quotation, a description, or an objection left standing.",
                "examples": [
                    "We timed the wash cycle before and after: 14 minutes down to 9 in the same sink.",
                    "The second enlarger head leaked too, and I still do not know from where.",
                ],
            },
        ),
        "symmetry_%d" % i: _noul(
            "Does %s contain a sentence whose two halves mirror each other?" % p,
            p,
            true={
                "what": "A sentence split by a comma, semicolon or conjunction into two halves "
                        "of near-equal length and parallel grammar; or a chiasmus in which "
                        "the same words return in reversed order.",
                "examples": [
                    "Ask not what your country can do for you, ask what you can do for your country.",
                    "The software adapts to your team instead of asking your team to adapt to it.",
                    "Where they saw a cost, we saw a signal.",
                ],
            },
            false={
                "what": "Sentences are lopsided: one clause carries most of the weight, or the "
                        "halves differ in grammar and length.",
                "examples": [
                    "It came out muddy twice before I found the light leak in the enlarger head.",
                    "If the developer runs cold, each print adds about 90 seconds.",
                ],
            },
        ),
    }


def piece_questions():
    return {
        "no_friction": _noul(
            "Is every problem that `piece` raises also resolved by `piece`?",
            "`piece`",
            true={
                "what": "Every difficulty, objection or open question the piece introduces is "
                        "answered or closed by its end. Nothing is admitted as unchecked, "
                        "unknown or unresolved.",
            },
            false={
                "what": "At least one thread is left open: a problem stated and not solved, an "
                        "objection left standing, a fact the writer says they did not check, "
                        "or a digression that goes nowhere.",
            },
        ),
        "template": _noul(
            "Does `piece` fill every slot of the standard template for a piece of its "
            "`genre`, in order, with no slot skipped and none doubled?",
            "`piece` against the conventional shape of `genre`",
            true={
                "what": "It reads as a form filled out: each conventional section of the genre "
                        "appears exactly once, in the conventional order. For a product review: "
                        "context, features, pros, cons, verdict. For a how-to: motivation, "
                        "prerequisites, numbered steps, troubleshooting, summary.",
            },
            false={
                "what": "Sections are missing, out of order or doubled; or the piece spends its "
                        "length unevenly, dwelling on one part and skipping others.",
            },
        ),
        "callback": _noul(
            "Does `piece` plant a specific detail early and recall the same detail at its close?",
            "the opening paragraphs and the final paragraph of `piece`",
            true={
                "what": "A distinctive detail (an object, a phrase, an image) appears near the "
                        "opening and reappears in the final paragraph so that the ending ties "
                        "back to the beginning.",
                "examples": ["'a drawer labeled in handwriting' in paragraph two, 'the drawer "
                             "labeled in handwriting' in the last paragraph"],
            },
            false={
                "what": "The ending does not return to an earlier detail, or details are "
                        "mentioned once and dropped.",
            },
        ),
        "texture": {
            "type": "score",
            "instructions": {
                "question": "Judging texture alone, with no knowledge of how `piece` was "
                            "produced, which description fits it best?",
                "inspect": "`piece`",
                "focus": "Shape and particularity, not correctness or quality.",
            },
            "criteria": [
                {
                    "what": "Uneven and particular. Paragraphs differ in length and shape; at "
                            "least one sentence is lopsided or awkward; the piece carries a "
                            "specific only its author could hold, such as a name, a date, a "
                            "number with its source, or a thing that went wrong and stayed "
                            "wrong; at least one thread is left open.",
                },
                {
                    "what": "Mostly particular. Some specifics only the author could supply and "
                            "some variety in paragraph shape, but occasional passages resolve "
                            "too neatly or fall into parallel shapes.",
                },
                {
                    "what": "Mostly uniform. Paragraphs land at similar length and shape, most "
                            "paragraphs close on a general line, specifics are few or generic, "
                            "and the argument proceeds without friction.",
                },
                {
                    "what": "Uniform throughout. Every paragraph is the same shape, every section "
                            "resolves on a quotable line, the piece contains no particular that "
                            "could not have been supplied by anyone, and it anticipates every "
                            "objection.",
                },
            ],
        },
    }


TEXTURE_LEGEND = ("uneven and particular", "mostly particular", "mostly uniform", "uniform throughout")


# ---------------------------------------------------------------------------
# Transport. One POST, retried on the two statuses the API documents as
# retryable. Injectable, so the tests never touch the network.
# ---------------------------------------------------------------------------
def api_key():
    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        raise JevUnavailable(
            f"{API_KEY_ENV} is not set. The Jev read needs a TypeSafe API key; create one "
            "at console.typesafe.ai and export it. Nothing was judged.")
    return key


def http_transport(payload, base_url=None, key=None, timeout=REQUEST_TIMEOUT):
    key = key or api_key()
    url = (base_url or os.environ.get(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/") + ENDPOINT
    body = json.dumps(payload).encode("utf-8")
    last = None
    for attempt, wait in enumerate(RETRY_BACKOFF + (None,)):
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": f"humanist-jev-read/{__version__}",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:  # noqa: BLE001 - the status is the message
                pass
            if e.code in RETRY_STATUSES and wait is not None:
                retry_after = e.headers.get("retry-after") if e.headers else None
                try:
                    wait = max(wait, float(retry_after)) if retry_after else wait
                except ValueError:
                    pass
                time.sleep(wait)
                last = e
                continue
            if e.code == 401:
                raise JevUnavailable("TypeSafe rejected the API key (401). Check TYPESAFE_API_KEY.")
            raise JevUnavailable(f"TypeSafe returned HTTP {e.code}: {detail or e.reason}")
        except urllib.error.URLError as e:
            raise JevUnavailable(f"could not reach {url}: {e.reason}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise JevUnavailable(f"TypeSafe returned a reply that is not JSON: {e}")
    raise JevUnavailable(f"TypeSafe kept returning {getattr(last, 'code', '?')} after retries.")


def ask(state, questions, transport, model):
    payload = {"state": state, "model": model, "questions": questions}
    reply = transport(payload)
    if not isinstance(reply, dict) or not isinstance(reply.get("answers"), dict):
        raise JevUnavailable("TypeSafe reply has no 'answers' map.")
    missing = [q for q in questions if q not in reply["answers"]]
    if missing:
        raise JevUnavailable(f"TypeSafe reply is missing {len(missing)} answer(s), e.g. {missing[0]!r}.")
    usage = reply.get("usage") or {}
    return reply["answers"], int(usage.get("input_tokens", 0) or 0), reply.get("model")


def _question_bytes():
    """Serialized size of one paragraph's four questions, measured once."""
    return len(json.dumps(paragraph_questions(0)))


def chunks(paras, max_paras=PARAGRAPHS_PER_REQUEST, max_bytes=BYTES_PER_REQUEST):
    """Split paragraph indices into request-sized runs. Always yields every index."""
    per_para = _question_bytes()
    out, run, size = [], [], 0
    for i, p in enumerate(paras):
        cost = per_para + 2 * len(p.encode("utf-8"))  # the paragraph and its closer
        if run and (len(run) >= max_paras or size + cost > max_bytes):
            out.append(run)
            run, size = [], 0
        run.append(i)
        size += cost
    if run:
        out.append(run)
    return out


def _noul_value(ans, qid):
    try:
        v = float(ans["noul"])
    except (KeyError, TypeError, ValueError):
        raise JevUnavailable(f"answer {qid!r} is not a noul.")
    return min(1.0, max(0.0, v))


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------
def read(t, genre="unspecified prose", transport=None, model=None, yes=YES,
         chunk=PARAGRAPHS_PER_REQUEST):
    """Run the Jev read over checker-ready text. Returns a plain dict.

    `t` is the markdown-stripped, soft-unwrapped text humanist.analyze produces.
    `transport` is a callable taking the request payload and returning the
    parsed reply; the default posts to TypeSafe. Raises JevUnavailable when the
    read cannot run, which callers map to exit 2.
    """
    transport = transport or http_transport
    model = model or os.environ.get(MODEL_ENV) or DEFAULT_MODEL
    paras = paragraphs(t)
    result = {
        "version": __version__, "model_requested": model, "model": None,
        "genre": genre, "paragraphs": len(paras), "yes_threshold": yes,
        "rhythm": rhythm_metrics(paras), "tells": {}, "texture": None,
        "requests": 0, "input_tokens": 0, "piece_truncated": False,
    }
    if not paras:
        result["skipped"] = "no prose paragraphs to judge"
        return result

    per_para = {tell: [None] * len(paras) for tell in PARAGRAPH_TELLS}
    for run in chunks(paras, max_paras=chunk):
        block = [paras[i] for i in run]
        state = {"paragraphs": block, "closers": [final_sentence(p) for p in block]}
        questions = {}
        for j in range(len(block)):
            questions.update(paragraph_questions(j))
        answers, tokens, reported = ask(state, questions, transport, model)
        result["requests"] += 1
        result["input_tokens"] += tokens
        result["model"] = reported or result["model"]
        for j, i in enumerate(run):
            for tell in PARAGRAPH_TELLS:
                qid = f"{tell}_{j}"
                per_para[tell][i] = _noul_value(answers[qid], qid)

    piece_words = _WORD.findall(" ".join(paras))
    piece = "\n\n".join(paras)
    if len(piece_words) > MAX_PIECE_WORDS:
        # Keep the opening and the close: the callback question needs both.
        head, tail = paras[: len(paras) // 3], paras[-(len(paras) // 3):]
        piece = "\n\n".join(head) + "\n\n[...]\n\n" + "\n\n".join(tail)
        result["piece_truncated"] = True
    answers, tokens, reported = ask({"genre": genre, "piece": piece}, piece_questions(), transport, model)
    result["requests"] += 1
    result["input_tokens"] += tokens
    result["model"] = reported or result["model"]

    for tell in PARAGRAPH_TELLS:
        probs = per_para[tell]
        hits = [i for i, p in enumerate(probs) if p > yes]
        top = max(range(len(probs)), key=lambda i: probs[i])
        result["tells"][tell] = {
            "name": TELL_NAMES[tell], "scope": "paragraph",
            "hits": len(hits), "of": len(probs), "share": len(hits) / len(probs),
            "mean_p": st.mean(probs), "probabilities": [round(p, 3) for p in probs],
            "example": (final_sentence(paras[top]) if tell == "closer" else paras[top])[:120],
            "example_p": probs[top],
        }
    for tell in ("no_friction", "template", "callback"):
        p = _noul_value(answers[tell], tell)
        result["tells"][tell] = {"name": TELL_NAMES[tell], "scope": "piece", "p": p, "hit": p > yes}

    tex = answers["texture"]
    try:
        probs = {int(k): float(v) for k, v in (tex.get("probabilities") or {}).items()}
        result["texture"] = {
            "score": float(tex["score"]), "max": len(TEXTURE_LEGEND) - 1,
            "confidence": float(tex.get("confidence", 0.0)),
            "probabilities": [round(probs.get(i, 0.0), 3) for i in range(len(TEXTURE_LEGEND))],
            "legend": list(TEXTURE_LEGEND),
        }
    except (KeyError, TypeError, ValueError):
        raise JevUnavailable("answer 'texture' is not a score.")
    return result


# ---------------------------------------------------------------------------
# Reporting. Densities and a texture score; never a verdict.
# ---------------------------------------------------------------------------
def _fmt_cv(v):
    return "UNTESTABLE" if v is None else f"{v:.2f}"


def report(r, out=None):
    out = out or sys.stdout
    w = lambda s="": print(s, file=out)  # noqa: E731
    w()
    w(f"JEV READ  |  {r['paragraphs']} paragraph(s), model {r.get('model') or r['model_requested']}, "
      f"{r['requests']} request(s), {r['input_tokens']:,} input tokens")
    if r.get("skipped"):
        w(f"  skipped: {r['skipped']}")
        return
    rh = r["rhythm"]
    w("  rhythm (computed in code, no model)")
    if rh["testable"]:
        w(f"    beat variation   sentences/paragraph CV {_fmt_cv(rh['sentences_per_paragraph_cv'])}, "
          f"words/paragraph CV {_fmt_cv(rh['words_per_paragraph_cv'])}   (low = uniform beat rate)")
    else:
        w(f"    beat variation   UNTESTABLE below {MIN_PARAGRAPHS_FOR_RHYTHM} paragraphs")
    w(f"    contractions     {rh['contractions_per_1k']:.1f} per 1k words")
    w(f"    numerals         {rh['numerals_per_100w']:.1f} per 100 words, gap CV {_fmt_cv(rh['numeral_gap_cv'])}"
      "   (dense and even = numbers as texture)")
    w(f"  tells (Jev, threshold p>{r['yes_threshold']})")
    for tell in PARAGRAPH_TELLS:
        d = r["tells"][tell]
        w(f"    {tell:11} {d['hits']:3d} of {d['of']:3d} paragraphs ({d['share']:.0%}), mean p {d['mean_p']:.2f}"
          f"   {d['name']}")
        w(f"                e.g. p={d['example_p']:.2f} {d['example']!r}")
    for tell in ("no_friction", "template", "callback"):
        d = r["tells"][tell]
        w(f"    {tell:11} p={d['p']:.2f} {'HIT ' if d['hit'] else '    '}  {d['name']}")
    tx = r["texture"]
    w(f"  texture          {tx['score']:.2f} of {tx['max']} toward '{TEXTURE_LEGEND[-1]}', "
      f"confidence {tx['confidence']:.2f}")
    w("                   " + "  ".join(f"{TEXTURE_LEGEND[i]} {p:.2f}" for i, p in enumerate(tx["probabilities"])))
    if r.get("piece_truncated"):
        w(f"  NOTE: piece-level questions saw the opening and closing thirds only "
          f"(over {MAX_PIECE_WORDS:,} words).")
    w("  These are densities for the composition read, not a verdict. Exit code is unchanged by them.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jev_read.py",
                                 description="The rhythm tells as typed judgments, via TypeSafe's Jev. Reports; never edits.")
    ap.add_argument("draft", help="prose draft (.md/.txt)")
    ap.add_argument("--genre", default="unspecified prose",
                    help="the piece's genre, for the template question (essay, how-to, review, email, marketing, social)")
    ap.add_argument("--json", action="store_true", help="emit the read as JSON")
    ap.add_argument("--model", default=None, help=f"model name (default ${MODEL_ENV} or {DEFAULT_MODEL})")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import humanist  # noqa: E402  - reuse the checker's markdown stripping so both read the same text
    raw = humanist.read_text(args.draft, "draft")
    t = humanist.strip_md(raw.replace("\ufeff", ""))
    try:
        r = read(t, genre=args.genre, model=args.model)
    except JevUnavailable as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, indent=1))
    else:
        report(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
