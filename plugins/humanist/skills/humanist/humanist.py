#!/usr/bin/env python3
"""
humanist.py - a mechanical prose sweep for AI writing tells.

  python humanist.py <draft.md> [--strip-quotes] [--lenient] [--mode post]
                     [--register NAME] [--config PATH] [--json]
  python humanist.py --calibrate <dir-of-your-own-writing> [--register NAME]
  python humanist.py --selftest
  python humanist.py --rules

WHAT IT IS. The middle stage of a three-stage pipeline: a subtractive rewrite pass
first, this mechanical sweep second, a human composition read last. It never edits.
It reports, and a person decides.

SEVERITY.
  FAIL  does not ship in public copy. Sets exit 1.
  WARN  judged in context; the count is reported so repetition stays visible.
  note  reported, never counted (what --lenient downgrades register rules to).

Exit codes: 0 clean, 1 one or more FAILs remain, 2 the tool could not do its job
(bad usage, unreadable file, unusable config). 2 is deliberately distinct from 1:
a crash that exits 1 is indistinguishable from an honest verdict, and the version
this tool was built from had exactly that defect.

WHY THE DEFAULTS LOOK LIKE THIS. An audit swept the previous rule set over 24
known-human documents (107,191 words, published 1854-2018) and found it blocked 22
of them. 94.6% of all 919 failures came from two rules - curly quotes and em dashes
- which describe how a file was encoded, not how it was written. Those two now
default to WARN. A checker that fails nine of ten published essays is not measuring
what it claims to, and a user who reads "199 FAIL" learns nothing and stops reading
the number.

The same audit found the zero was unreliable in the other direction too:
  - A curly apostrophe defeated 12 of 41 rules, because their patterns embed a
    literal ASCII quote and `re` does no quote folding - and this tool's own
    html2prose.py produces curly apostrophes by design. Quotes are now folded
    before matching, and the curly-quote rule counts from the raw text.
  - A UTF-8 BOM (what PowerShell 5.1 `Set-Content -Encoding utf8` writes) silently
    disabled every line-anchored rule on the first line. All reads are utf-8-sig.
  - The unicode-arrow rule crashed the reporter on a cp1252 console: the one rule
    whose whole purpose is catching arrows was the rule that killed the process
    when it fired, and through the documented web-copy pipeline that crash
    produced "CLEAN" on a zero-byte file. stdout is reconfigured, guarded.
  - The negative-parallelism rule missed three of the five forms its own name
    claimed, including two printed as examples in ai-tropes.md.

DESIGN NOTES.
  - Soft line breaks are unwrapped before matching. A hard-wrapped draft defeats
    every multi-word pattern otherwise: "anything that\\npromises" is invisible to
    \\banything that promises\\b. Paragraph breaks and headings survive.
  - severity_overrides match a rule's stable ID exactly, never by substring. The
    previous substring match meant a key of "often" silently disabled an unrelated
    rule. Run --rules to list every ID.
  - Every run prints its own frame: word count, config path, how many rules are
    active, how many were overridden. A partial run cannot be reported as a full
    one, and a suppressed rule set cannot masquerade as a clean sweep.

CALIBRATION. --calibrate reads .md/.txt files of YOUR OWN published writing, one
register per run, and writes humanist.config.json with provenance. Marker bands are
a normal approximation to the Poisson interval, widened 15%. Until calibrated,
--mode post uses wide generic bands and says UNCALIBRATED in the output.

SAMPLING LAW: a rare-event rate cannot be tested below the word count that yields
an expected count of ~3. Below that the marker prints UNTESTABLE, not a number.
"""
import argparse
import json
import math
import os
import re
import statistics as st
import sys
from datetime import date

CONFIG_NAME = "humanist.config.json"
__version__ = "0.1.0"

EXIT_CLEAN, EXIT_FAILS, EXIT_ERROR = 0, 1, 2


def _reconfigure_streams():
    """Force UTF-8 on stdout and stderr.

    Guarded, because the attribute is absent on a StringIO-captured stream and
    main() is explicitly callable programmatically. errors="backslashreplace"
    rather than "replace" is deliberate: "replace" prints '?' for every
    un-encodable character, so the report for the arrow rule would read e.g. '?'
    and the writer could not tell which arrow to delete.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError, OSError):
            pass


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(EXIT_ERROR)


def read_text(path, what="file"):
    """Read a text file, tolerating a BOM and failing loudly on anything else.

    utf-8-sig is byte-identical to utf-8 on a BOM-less file, so this has no
    regression surface. It is not optional: a BOM is what several Windows tools
    write by default, U+FEFF is not whitespace to re or str.strip, and its
    presence silently disabled five line-anchored FAIL rules in the previous
    version.
    """
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return fh.read()
    except FileNotFoundError:
        die(f"no such {what}: {path}")
    except IsADirectoryError:
        die(f"{path} is a directory, not a {what}")
    except UnicodeDecodeError as e:
        die(f"{path} is not valid UTF-8 ({e.reason} at byte {e.start}). Re-save it "
            "as UTF-8. Decoding with replacement characters would turn a loud "
            "failure into a wrong verdict, so this tool refuses to.")
    except OSError as e:
        die(f"could not read {path}: {e}")


# ---------------------------------------------------------------------------
# HOUSE CONFIG. Your house's taste lives here, or in the "house" section of
# humanist.config.json, which overrides it. Everything below ships generic.
# ---------------------------------------------------------------------------
HOUSE_CONFIG = {
    "extra_banned_words": [],
    "extra_warn_words": [],
    "never_flag_words": [],
    "extra_ai_vocab": [],
    "exempt_patterns": [],
    # Keys are rule IDs (see --rules), matched EXACTLY. Values: FAIL | WARN | off.
    "severity_overrides": {},
    # Readability. Checked and reported as a WARN, not merely printed. The previous
    # version printed these next to the word "targets" and compared nothing, so a
    # draft at grade 38 exited CLEAN.
    "fk_quotable": 8,
    "fk_body": 10,
    "check_readability": True,
    "syllable_overrides": {},
}

OVERRIDES = {"queue": 1, "poetry": 3, "api": 3, "url": 3, "ai": 2, "gui": 3,
             "one": 1, "once": 1, "you": 1, "your": 1, "the": 1, "are": 1}

# Curly to straight, applied before matching because many rules below embed a
# literal ASCII quote and Python re does no quote folding. No shipped pattern
# contains a literal straight double quote, so folding that pair is safe.
QUOTE_FOLD = {0x2018: 0x27, 0x2019: 0x27, 0x201A: 0x27, 0x201B: 0x27,
              0x201C: 0x22, 0x201D: 0x22, 0x201E: 0x22, 0x201F: 0x22,
              0x2032: 0x27, 0x2033: 0x22}


def syllables(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w:
        return 0
    if w in OVERRIDES:
        return OVERRIDES[w]
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def fk(t):
    """Flesch-Kincaid grade level, with its frame.

    A heuristic syllable counter moves the grade by a few tenths against a
    dictionary counter; direction holds. This is an audience-friction measure, not
    a voice measurement: a real voice at grade 9 beats slop at grade 6.
    """
    words = re.findall(r"[A-Za-z][A-Za-z']*", t)
    if not words:
        return 0.0, 0
    for a in ["e.g.", "i.e.", "etc.", "Mr.", "Mrs.", "Dr.", "vs.", "St."]:
        t = t.replace(a, a.replace(".", ""))
    sen = max(1, len([x for x in re.split(r"[.!?]+(?:\s|$)", t) if x.strip()]))
    grade = 0.39 * (len(words) / sen) + 11.8 * (sum(map(syllables, words)) / len(words)) - 15.59
    return max(0.0, round(grade, 1)), len(words)


def strip_md(t):
    """Reduce markdown to the prose the rules should see."""
    t = t.translate(QUOTE_FOLD)
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = re.sub(r"^\s*\|.*\|\s*$", "", t, flags=re.M)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"https?://\S+", "", t)
    # Unwrap soft line breaks; keep paragraph breaks, headings and list markers.
    t = re.sub(r"(?<!\n)\n(?!\n|#|\s*[-*+>]|\s*\d+\.)", " ", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t


# ---------------------------------------------------------------------------
# RULES:  (id, name, severity, pattern, flags, register)
#
# `id` is stable and is what severity_overrides matches, exactly.
#
# `register` says which laws a rule belongs to, so --lenient can relax the ones
# genuinely about public-copy presentation without silencing rules about
# substance. The previous version keyed that off whether the literal substring
# "[law]" appeared in the display name, so "[law 4]" did not match and the relief
# was effectively random: 8 of 14 law rules got none, including curly quotes.
#
#   universal  a tell in any register. Never relaxed.
#   format     presentation. Internal docs legitimately differ. --lenient relaxes.
#   phrasing   public-copy register. --lenient relaxes.
# ---------------------------------------------------------------------------
NEG_PARALLEL = "|".join([
    # inline, uncontracted
    r"\b(?:it'?s|that'?s|this is|it is|that is) not (?:just |simply |merely |only |about )?[^.?!\n]{2,60}[,;] ?(?:it'?s|that'?s|this is|it is|but)\b",
    # inline, CONTRACTED. Branch 1 required the uncontracted form, so the exact
    # example ai-tropes.md prints was unreachable.
    r"\b(?:it|that|this|there|they)\s?(?:'s)?\s?(?:is|are|was|were)n'?t\s+(?:just |simply |merely |only |about )?[^.?!\n]{2,60}[,;]\s?(?:it'?s|that'?s|this is|it is|but)\b",
    # scaled
    r"\bnot (?:just|simply|merely|only) [^.?!\n]{2,60}[, ]but\b",
    r"\bnot because [^.?!\n]{2,50}, but because\b",
    r"\bless about [^.?!\n]{2,40}(?:,| and) more about\b",
    # sentence-split, present OR PAST tense second clause. The doc's own split
    # example is past tense, which the old branch could not reach.
    r"\bThe [a-z]+ (?:is|was|are|were)n'?t [^.?!\n]{2,50}\.\s*The [a-z]+ (?:is|was|are|were)\b",
    r"\b(?:is|are|was|were)n'?t [^.?!\n]{2,60}\.\s*(?:It|That|This|What [a-z ]{3,30}) (?:is|are|was|were|does|do|did)\b",
    r"\b(?:It|That|This) (?:is|was) not [^.?!\n]{2,60}\.\s*(?:It|That|This|What [a-z ]{3,30}) (?:is|are|was|were|does|do|did)\b",
    # sentence-split with a contracted opener: "It's not a warehouse. It's a service."
    r"\b(?:It|That|This)'?s not (?:just |simply |merely |only )?(?:a|an|the) [^.?!\n]{2,50}\.\s*(?:It|That|This)'?s (?:a|an|the)\b",
    # negated appositive, BOTH orders. The old branch required the negated half
    # first, so the doc's own example form was unreachable.
    r"\bnot (?:a|an|the) [^.?!\n]{2,40}[,;] (?:a|an|the)\b",
    r"\b(?:is|was|are|were) (?:a|an|the) [a-z][^.?!\n]{2,40}, not (?:a|an|the) [a-z]",
])

CHECKS = [
    ("self-justify-rather", "self-justification: I'd-rather-X-than-Y", "FAIL",
     r"\bI(?:'d| would| had) rather\b[^.?!\n]{2,90}\bthan\b", re.I, "phrasing"),
    ("self-justify-whole", "self-justification: that-is-the-whole-X", "FAIL",
     r"\b(?:that|this)(?:'s| is| was) the whole (?:reason|argument|point|thing)\b", re.I, "phrasing"),
    ("virtue-claim", "virtue-claim: announcing your own honesty", "FAIL",
     r"\bI(?:'m| am)? ?(?:'?m)? ?not going to (?:pretend|call it|claim|guess|invent)\b|\band I'?ll say so\b", re.I, "phrasing"),
    ("pre-argument", "pre-argument: weighing evidence before showing it", "FAIL",
     r"\b(?:two|three|four|five|six|seven) (?:things|notes|points|reasons)\b[^.?!\n]{0,40}\b(?:say it|on this|here)\b|\bwhat I can tell you is\b", re.I, "phrasing"),
    ("worth-knowing", "worth-knowing tell", "FAIL", r"\bworth knowing\b", re.I, "phrasing"),
    ("announce-move", "announcing the move before making it", "WARN",
     r"\bso I'?ll head it off\b|\bI'?ll (?:explain|walk you through|lay out) (?:that|this|it) (?:below|now)\b", re.I, "phrasing"),

    # ---- Typography. WARN, not FAIL, and this is the most consequential default
    # in the file. On 107,191 words of published human prose these produced 869 of
    # 919 total failures and 869 of 869 adjudicated false positives. They describe
    # the encoder, not the writer. Promote them if your house genuinely bans them.
    ("em-dash", "em/en dash", "WARN", r"[—–]", 0, "format"),
    ("curly-quotes", "smart/curly quotes", "WARN", r"[‘’“”]", 0, "format"),
    ("unicode-arrows", "unicode arrows", "WARN", r"[→⇒▸➔]", 0, "format"),

    # ---- AI vocabulary, in two tiers, because the single flat FAIL list was the
    # second-largest false-positive source on the human corpus and every one of
    # its 15 hits there was ordinary English: Obergefell's "fostered and then
    # adopted a baby boy" (foster care), the Rogers Commission's "crucial
    # information about the O-ring damage", Thoreau's "elevate his life", RFC
    # 793's "utilize the SYN control flag". A blanket ban on a common English word
    # is house taste, not universal law, and belongs in extra_banned_words.
    #
    # Tier 1 FAIL: constructions with essentially no innocent use in contemporary
    # prose. Anchored, not bare words, so a literal tapestry and a real testament
    # both survive.
    ("ai-vocab-strong", "AI vocab (unambiguous)", "FAIL",
     r"\bdelv(?:e|es|ed|ing)\b"
     r"|\b(?:rich|complex|intricate|vibrant|broader) tapestry\b"
     r"|\b(?:a|is a|stands as a) testament to\b"
     r"|\bin today'?s fast[- ]paced\b"
     r"|\bever[- ](?:evolving|changing|growing) landscape\b"
     r"|\bnavigat(?:e|es|ing) the (?:complex|complexities|ever)\b"
     r"|\bat the end of the day,\b", re.I, "universal"),
    # Tier 2 WARN: real markers of machine drafting whose literal senses are
    # ordinary. Counted, so repetition stays visible, which is the actual tell.
    ("ai-vocab", "AI vocab (has legitimate senses; watch the density)", "WARN",
     r"\b(crucial|pivotal|underscor(?:e|es|ed|ing)|showcas(?:e|es|ed|ing)|vibrant|"
     r"seamless(?:ly)?|elevat(?:e|es|ed|ing)|unlock(?:ing|ed|s)?|foster(?:ing|ed|s)?|"
     r"garner(?:ing|ed|s)?|utiliz(?:e|es|ed|ing)|streamlin(?:e|es|ed|ing)|"
     r"(?<!-)leverag(?:e|es|ed|ing)|robust|harness(?:es|ed|ing)?)\b", re.I, "phrasing"),
    ("magic-adverbs", "magic adverbs", "WARN", r"\b(deeply|fundamentally|remarkably|arguably)\b", re.I, "phrasing"),
    ("ornate-noun", "ornate-noun (abstract)", "WARN", r"\b(paradigm|synergy|ecosystems?)\b", re.I, "phrasing"),
    ("serves-as", "serves-as dodge", "WARN",
     r"\b(serves as|stands as|marks a pivotal|represents a (?:pivotal|significant))\b", re.I, "phrasing"),

    # WARN, not FAIL, and the demotion is evidence-driven rather than a softening.
    # Detection was widened (it now catches all five documented forms; it used to
    # miss three), but on 107k words of human prose 10 of its 17 hits were the
    # correlative "not only X but Y" as written by Thoreau, Du Bois, Russell and
    # by Strunk in Elements of Style: "This is true not only in narrative
    # principally concerned with action, but in writing of any kind." That is
    # standard English. The actual tell is the DEFINITIONAL substitution - "it's
    # not a headset, it's a paradigm shift" - and no regex separates the two
    # reliably. ai-tropes.md already states the right disposition for this family:
    # any of these once might be fine, and one repeatedly is the tell. A counted
    # WARN says exactly that; a FAIL says something the evidence does not support.
    ("neg-parallel", "negative parallelism / not-X-but-Y (count matters more than any single hit)",
     "WARN", NEG_PARALLEL, re.I, "universal"),
    ("antithesis-lite", "antithesis-lite (X rather than Y)", "WARN",
     r"\b(?:is|are|was|were|it'?s|that'?s)\s+(?:a |an |the )?[a-z]+(?:\s+[a-z]+)?\s+rather than\b", re.I, "phrasing"),

    ("fake-candid", "fake-candid opener", "FAIL",
     r"\bto be honest\b|\bI'?ll be honest\b|\bthe honest answer is\b|(?:^|[.!?]\s+)Honestly\?", re.I | re.M, "universal"),
    ("not-x-not-y", "Not X. Not Y. Just Z.", "FAIL",
     r"\bNot [^.?!\n]{1,40}\. Not [^.?!\n]{1,40}\.\s*(?:Just|It'?s|A|An)\b", 0, "universal"),
    ("drama-question", "self-answered drama question", "FAIL",
     r"\bThe (?:result|kicker|catch|problem|truth|worst part|best part|scary part|crazy part)\?", re.I, "universal"),
    ("worth-noting", "it's-worth-noting filler", "FAIL",
     r"\b(it'?s worth noting|it bears mentioning)\b|(?:^|\. )(Importantly|Interestingly|Notably),", re.I | re.M, "universal"),
    ("ing-tail", "-ing significance tail", "FAIL",
     r",\s+(?:highlighting|underscoring|reflecting|showcasing|demonstrating|cementing|solidifying)\s+(?:its|the|their|a)\b", re.I, "universal"),
    ("false-range", "false range (from-to-to)", "WARN",
     r"\bfrom [a-z-]+(?: [a-z-]+)? to [a-z-]+(?: [a-z-]+)? to [a-z-]+", re.I, "phrasing"),
    ("listicle", "listicle in a trench coat", "WARN", r"\bThe (?:first|second|third|fourth) [a-z]+ is\b", 0, "phrasing"),
    ("kicker", "here's-the-kicker suspense", "FAIL",
     r"\bhere'?s the (?:kicker|deal)\b|\bhere'?s the thing\b|\bhere'?s (?:where it gets interesting|what most people miss)\b", re.I, "universal"),
    ("think-of-it", "think-of-it-as analogy", "WARN", r"\bthink of it (?:as|like)\b|\bit'?s like a\b", re.I, "phrasing"),
    ("imagine-world", "imagine-a-world futurism", "FAIL", r"\bimagine a world where\b|\bin that world,\b", re.I, "universal"),
    ("truth-is-simple", "truth-is-simple assertion", "FAIL",
     r"\bthe (?:reality|truth|answer) is simple\b|\bhistory is (?:clear|unambiguous)\b|\bthe (?:metrics|examples|data) are clear\b", re.I, "universal"),
    ("stakes-inflation", "stakes inflation", "FAIL",
     r"\bfundamentally (?:reshape|transform|change)\b|\bdefine the next era\b|\bchange everything\b", re.I, "universal"),
    ("break-it-down", "let's-break-this-down", "FAIL",
     r"\blet'?s (?:break (?:this|it|that) down|unpack|dive in|dive deeper|explore)\b|\bwithout further ado\b", re.I, "universal"),
    ("vague-attribution", "vague attribution (name it AND link it)", "FAIL",
     r"\bexperts (?:argue|say|agree|suggest)\b|\bindustry reports?\b|\bobservers (?:have )?(?:cited|note[d]?)\b|\bstudies (?:show|suggest|indicate)\b|\bresearch shows\b", re.I, "universal"),
    ("invented-label", "invented concept label", "WARN",
     r"\bthe [a-z]+ (?:paradox|trap|creep|divide|vacuum|inversion)\b", re.I, "phrasing"),
    # Register-dependent, so it lives in "phrasing" and --lenient relaxes it. In a
    # public essay "In conclusion" is a genuine tell. In a specification it is
    # section structure: both of its corpus hits were RFC 3439 and Feynman's
    # appendix to the Rogers Commission report, where it is doing real work.
    ("signposted-conclusion", "signposted conclusion", "FAIL",
     r"\b(in conclusion|to sum up|in summary)\b", re.I, "phrasing"),
    ("despite-challenges", "despite-its-challenges formula", "FAIL",
     r"\bdespite (?:these|its|their) [^.?!\n]{0,40}challenges\b", re.I, "universal"),
    ("vague-often", "'often' vague-frequency", "WARN",
     r"(?<![0-9]x as )(?<!how )\boften\b", re.I, "phrasing"),

    # ---- The law-5 family: a sentence ABOUT the material instead of the material.
    ("verdict-preamble", "verdict-preamble: announcing that what follows matters", "FAIL",
     r"\bone (?:thing|boundary|point|caveat|qualifier|detail)\s+(?:that\s+)?(?:matters|is worth|to note)\b|\bwhat matters here\b|\bthe (?:key|important|crucial) (?:point|part|thing|lesson)\b|\bthe real (?:point|lesson|takeaway)\b|\bworth remembering\b", re.I, "phrasing"),
    # Downgraded to WARN: "Note that..." is standing reference style in technical
    # documentation, and this rule was a top false-positive producer on the corpus.
    ("reader-instruction", "reader-instruction: telling the reader how to read", "WARN",
     r"(?:^|[.!?]\s+)(?:Read|Note|Notice|Remember|Consider|Keep in mind)\s+(?:that|this|it)\b", re.M, "phrasing"),
    ("self-justifying-heading", "self-justifying heading", "FAIL",
     r"^#{1,6}\s+.*\b(?:because|so that|which is why|and why)\b", re.I | re.M, "phrasing"),
    ("doubled-heading", "doubled heading (X, and Y)", "WARN", r"^#{1,6}\s+[^,\n]+,\s+and\s+\S+", re.I | re.M, "format"),
    ("verdict-frame", "verdict frame: a conclusion about the material", "FAIL",
     r"(?:^|[.!?]\s+)(?:that is (?:the point|the lesson|what matters|why)|this is (?:the point|the lesson))\b|\bthe (?:takeaway|upshot) (?:is|here)\b", re.I | re.M, "phrasing"),
    ("throat-clearing", "throat-clearing transition", "FAIL",
     r"(?:^|[.!?]\s+)(?:with that (?:established|said)|that said,|now that we|having (?:established|said)|before we (?:get|dive))\b", re.I | re.M, "phrasing"),
    ("unnamed-swipe", "swipe at unnamed others", "WARN",
     r"\b(?:most|other|every)\s+(?:coverage|takes?|threads?|writers?|people)\s+(?:will|would|has|have|are|is)\b|\bthe coverage will\b", re.I, "phrasing"),
    # 6+ letters and a function-word exclusion. The old 4+ version matched pronouns
    # and connectives on both sides of "because" and produced constant noise.
    ("circular-because", "circular causal: same content word on both sides of 'because'", "WARN",
     r"\b(?!because|through|between|another|however|therefore|although|whether)([a-z]{6,})\b[^.?!\n]{0,70}\bbecause\b[^.?!\n]{0,70}\b\1\b", re.I, "phrasing"),
]

REGISTER_RELAXED_BY_LENIENT = {"format", "phrasing"}
VALID_SEVERITIES = {"FAIL", "WARN", "OFF"}


def rule_ids():
    return [c[0] for c in CHECKS]


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------
def anaphora(t):
    """Runs of 3 or more consecutive sentences opening with the same two words."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]

    def head(s):
        # Normalized tokens, so one comma does not defeat the check.
        return tuple(re.findall(r"[A-Za-z']+", s.lower())[:2])

    heads = [head(s) for s in sents]
    runs, i = [], 0
    while i < len(heads) - 2:
        h = heads[i]
        if len(h) < 2 or h[0] in ("i", "the", "a", "it"):
            i += 1
            continue
        n = 1
        while i + n < len(heads) and heads[i + n] == h:
            n += 1
        if n >= 3:
            runs.append(" ".join(h))
            i += n
        else:
            i += 1
    return runs


def dup_sentences(t):
    sents = [s.strip().lower() for s in re.split(r"(?<=[.!?])\s+", t) if len(s.split()) > 8]
    seen, dups = set(), []
    for s in sents:
        if s in seen:
            dups.append(s[:60])
        seen.add(s)
    return dups


def bold_bullets(raw):
    """Bullets opening with a bolded keyword, ignoring fenced code blocks."""
    raw = re.sub(r"```.*?```", "", raw, flags=re.S)
    return len(re.findall(r"^\s*[-*+]\s+\*\*", raw, re.M))


# ---------------------------------------------------------------------------
# --mode post: register bands
# ---------------------------------------------------------------------------
DEFAULT_MARKERS = {"I": r"\bi\b", "you": r"\byou\b", "your": r"\byour\b",
                   "so": r"\bso\b", "just": r"\bjust\b"}
GENERIC_BANDS = {
    "med": (11, 21, "median sentence words (generic sanity range)"),
    "le5": (2, 25, "% sentences <=5 words (generic sanity range)"),
    "gt20": (10, 40, "% sentences >20 words (generic sanity range)"),
    "I": (2.0, 40.0, "'I' per 1k (generic sanity range)"),
    "you": (2.0, 45.0, "'you' per 1k (generic sanity range)"),
    "your": (1.0, 30.0, "'your' per 1k (generic sanity range)"),
    "so": (0.5, 10.0, "'so' per 1k (generic sanity range)"),
    "just": (0.5, 10.0, "'just' per 1k (generic sanity range)"),
}
STRUCTURAL = ("med", "le5", "gt20")


def generic_min_words():
    mw = {}
    for k, (lo, hi, _) in GENERIC_BANDS.items():
        if k in STRUCTURAL:
            continue
        mid = (lo + hi) / 2.0
        mw[k] = int(math.ceil(3000.0 / mid)) if mid > 0 else 10 ** 9
    return mw


def post_stats(t, markers):
    w = re.findall(r"[A-Za-z']+", t.lower())
    if not w:
        return None
    sents = [x for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]
    lens = [len(re.findall(r"[A-Za-z']+", s)) for s in sents] or [0]
    K = 1000 / len(w)
    joined = " ".join(w)
    out = dict(nwords=len(w), nsents=len(lens), med=st.median(lens),
               le5=100 * sum(1 for l in lens if l <= 5) / len(lens),
               gt20=100 * sum(1 for l in lens if l > 20) / len(lens))
    for k, pat in markers.items():
        out[k] = len(re.findall(pat, joined)) * K
    return out


def poisson_band(count, nwords):
    """Normal approximation to the Poisson interval, widened 15%, per 1k words.

    Named honestly: this is the Wald/normal approximation, not an exact Poisson
    interval. It is adequate at the counts calibration actually sees and poor
    below about ten, which is what the min_words threshold exists to keep you
    away from. count == 0 uses the rule of three.
    """
    if count > 0:
        half = 1.96 * math.sqrt(count)
        lo_c, hi_c = max(0.0, count - half * 1.15), count + half * 1.15
    else:
        lo_c, hi_c = 0.0, 3.0 * 1.15
    k = 1000.0 / nwords
    return round(lo_c * k, 1), round(hi_c * k, 1)


def prop_band(pct, nsents):
    p = pct / 100.0
    half = 1.96 * math.sqrt(max(p * (1 - p), 0.0) / max(nsents, 1)) * 1.15
    return round(max(0.0, p - half) * 100, 1), round(min(1.0, p + half) * 100, 1)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def default_config_path(explicit=None):
    if explicit:
        return explicit
    for cand in (os.path.join(os.getcwd(), CONFIG_NAME),
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_NAME)):
        if os.path.exists(cand):
            return cand
    return os.path.join(os.getcwd(), CONFIG_NAME)


def validate_house(house, path):
    """Fail loudly on a config that cannot mean what it says.

    A mistyped severity or an unknown rule ID used to be accepted silently, which
    turned a FAIL into an uncounted note and let the run report CLEAN.
    """
    ids = set(rule_ids())
    overrides = house.get("severity_overrides", {})
    if not isinstance(overrides, dict):
        die("severity_overrides must be an object mapping rule ID -> FAIL|WARN|off")
    fixed = {}
    for key, val in overrides.items():
        if key not in ids:
            near = [i for i in sorted(ids) if key.lower() in i or i in key.lower()]
            hint = f" Did you mean: {', '.join(near[:4])}?" if near else ""
            die(f"severity_overrides names an unknown rule ID {key!r}"
                f"{' in ' + path if path else ''}.{hint} Run --rules for the list.")
        if not isinstance(val, str) or val.strip().upper() not in VALID_SEVERITIES:
            die(f"severity_overrides[{key!r}] is {val!r}; must be FAIL, WARN or off.")
        fixed[key] = val.strip().upper()
    house["severity_overrides"] = fixed
    for k in ("extra_banned_words", "extra_warn_words", "never_flag_words",
              "extra_ai_vocab", "exempt_patterns"):
        if not isinstance(house.get(k, []), list):
            die(f"house.{k} must be a list of strings.")
    for pat in house.get("exempt_patterns", []):
        try:
            re.compile(pat)
        except re.error as e:
            die(f"exempt_patterns entry {pat!r} is not a valid regex: {e}")


def load_config(path):
    cfg = {"house": dict(HOUSE_CONFIG), "band_sets": {}, "markers": dict(DEFAULT_MARKERS),
           "path": path, "loaded": False, "override_count": 0}
    if path and os.path.exists(path):
        try:
            data = json.loads(read_text(path, "config"))
        except json.JSONDecodeError as e:
            # Loud, not swallowed. A config that silently fails to load takes
            # severity_overrides, never_flag_words and exempt_patterns with it,
            # and the run then reports a verdict computed under rules the user
            # believes they replaced.
            die(f"{path} is not valid JSON: {e}. Fix it or pass a different "
                "--config. Continuing with built-in defaults would report a "
                "verdict under rules you did not choose.")
        if not isinstance(data, dict):
            die(f"{path} must contain a JSON object at the top level.")
        cfg["house"].update({k: v for k, v in data.get("house", {}).items()
                             if not k.startswith("_")})
        cfg["band_sets"] = data.get("band_sets", {})
        if data.get("markers"):
            cfg["markers"] = data["markers"]
        cfg["loaded"] = True
    validate_house(cfg["house"], cfg["path"] if cfg["loaded"] else None)
    OVERRIDES.update(cfg["house"].get("syllable_overrides", {}))
    cfg["override_count"] = len(cfg["house"].get("severity_overrides", {}))
    return cfg


def calibrate(dirpath, register, cfg):
    if not os.path.isdir(dirpath):
        die(f"--calibrate needs a directory of your own writing; {dirpath} is not one.")
    files = sorted(f for f in os.listdir(dirpath) if f.lower().endswith((".md", ".txt")))
    if not files:
        die(f"no .md/.txt files in {dirpath}.")
    corpus = "\n\n".join(strip_md(read_text(os.path.join(dirpath, f), "corpus file"))
                         for f in files)
    s = post_stats(corpus, cfg["markers"])
    if not s or s["nwords"] < 300:
        die(f"calibration corpus too small ({0 if not s else s['nwords']} words). "
            "Supply more of your own writing.")
    n, nsents = s["nwords"], s["nsents"]
    joined = " ".join(re.findall(r"[A-Za-z']+", corpus.lower()))
    bands, min_words = {}, {}
    bands["med"] = [round(s["med"] * 0.8), round(s["med"] * 1.2),
                    f"median sentence words (measured {s['med']:.1f}; band = +/-20%)"]
    for k in ("le5", "gt20"):
        lo, hi = prop_band(s[k], nsents)
        bands[k] = [lo, hi, f"% sentences {'<=5' if k == 'le5' else '>20'} words "
                            f"(measured {s[k]:.1f}; normal approx widened 15%)"]
    for k, pat in cfg["markers"].items():
        c = len(re.findall(pat, joined))
        lo, hi = poisson_band(c, n)
        bands[k] = [lo, hi, f"'{k}' per 1k (measured {c * 1000 / n:.1f}; normal approx widened 15%)"]
        min_words[k] = int(math.ceil(3.0 * n / c)) if c > 0 else None

    path = cfg["path"]
    existing = {}
    if os.path.exists(path):
        raw = read_text(path, "config")
        if raw.strip():
            try:
                existing = json.loads(raw)
            except json.JSONDecodeError as e:
                # Never clobber. This file is the only persistent state the tool
                # has, and destroying it behind a success message is not a thing a
                # reporting tool gets to do.
                die(f"{path} exists but is not valid JSON ({e}). Refusing to "
                    "overwrite it and lose your bands and house config. Fix or "
                    "move that file, then re-run --calibrate.")
        if not isinstance(existing, dict):
            die(f"{path} exists but is not a JSON object. Refusing to overwrite it.")
    existing.setdefault("house", {})
    existing.setdefault("markers", cfg["markers"])
    existing.setdefault("band_sets", {})[register] = {
        "provenance": {"sources": files, "files": len(files), "words": n,
                       "date": date.today().isoformat()},
        "bands": bands,
        "min_words": min_words,
    }
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(existing, f, indent=1)
        f.write("\n")
    print(f"CALIBRATED band set '{register}' from {len(files)} file(s), {n:,} words, "
          f"{date.today().isoformat()}.")
    print(f"Written to {path}. Later runs load it automatically.")
    print("Measure published writing, not chat logs: collaborator and chat corpora")
    print("over-predict first person and question rate.")
    for k, v in bands.items():
        lo, hi, d = v
        mw = min_words.get(k)
        print(f"  {k:9} band {lo}-{hi}" + (f"  min testable {mw:,}w" if mw else "") + f"  ({d})")


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def build_checks(house):
    checks = list(CHECKS)
    if house.get("extra_ai_vocab"):
        pat = r"\b(?:" + "|".join(re.escape(w) for w in house["extra_ai_vocab"]) + r")\b"
        checks.append(("house-ai-vocab", "AI vocab (house-extended)", "FAIL", pat, re.I, "universal"))
    if house.get("extra_banned_words"):
        pat = r"\b(?:" + "|".join(re.escape(w) for w in house["extra_banned_words"]) + r")\b"
        checks.append(("house-banned", "house banned word", "FAIL", pat, re.I, "phrasing"))
    if house.get("extra_warn_words"):
        pat = r"\b(?:" + "|".join(re.escape(w) for w in house["extra_warn_words"]) + r")\b"
        checks.append(("house-warn", "house warn word", "WARN", pat, re.I, "phrasing"))
    out = []
    for rid, name, sev, pat, fl, reg in checks:
        sev = house.get("severity_overrides", {}).get(rid, sev)
        if sev == "OFF":
            continue
        out.append((rid, name, sev, pat, fl, reg))
    return out


def analyze(raw, house, lenient=False, strip_quotes=False):
    # Belt and braces on the BOM. read_text() strips it at the file layer via
    # utf-8-sig, but analyze() is a public entry point and a caller who read the
    # text some other way would otherwise hit the original defect: U+FEFF is not
    # whitespace to re or str.strip, so a leading BOM silently disables every
    # line-anchored rule on the first line and hides the first blockquote from
    # --strip-quotes. Stripping it here means no caller can reintroduce that.
    raw = raw.replace("﻿", "")
    quote_lines = 0
    if strip_quotes:
        lines = raw.split("\n")
        quote_lines = len([l for l in lines if l.strip().startswith(">")])
        raw = "\n".join(l for l in lines if not l.strip().startswith(">"))
    t = strip_md(raw)
    grade, words = fk(t)
    never = {x.lower() for x in house.get("never_flag_words", [])}
    exempts = [re.compile(p, re.I) for p in house.get("exempt_patterns", [])]
    findings, fails, warns = [], 0, 0
    active = build_checks(house)

    for rid, name, sev, pat, fl, reg in active:
        # The curly-quote rule is the one rule that must see the ORIGINAL text,
        # because strip_md folds exactly the characters it looks for. bold_bullets
        # takes the same approach for the same reason.
        subject = raw if rid == "curly-quotes" else t
        ms = list(re.finditer(pat, subject, fl))
        if never:
            ms = [m for m in ms if m.group(0).strip().lower().strip(".,;:!?\"'") not in never]
        if exempts:
            ms = [m for m in ms if not any(x.match(subject[m.start():m.end() + 80]) for x in exempts)]
        if not ms:
            continue
        eff = sev
        if lenient and reg in REGISTER_RELAXED_BY_LENIENT and sev == "FAIL":
            eff = "note"
        n = len(ms)
        if eff == "FAIL":
            fails += n
        elif eff == "WARN":
            warns += n
        findings.append((rid, name, eff, n, ms[0].group(0)[:50]))

    a = anaphora(t)
    if a:
        warns += len(a)
        findings.append(("anaphora", "anaphora (3+ same openings)", "WARN", len(a), str(a[:3])))
    d = dup_sentences(t)
    if d:
        fails += len(d)
        findings.append(("dup-sentence", "duplicated sentence", "FAIL", len(d), d[0]))
    b = bold_bullets(raw)
    if b >= 3:
        eff = "note" if lenient else "WARN"
        if eff == "WARN":
            warns += 1
        findings.append(("bold-bullets", "bold-first bullets in public copy", eff, b,
                         f"{b} bold-first bullets"))

    # Readability, actually compared rather than merely printed.
    if house.get("check_readability", True) and words >= 100:
        limit = house.get("fk_body", 10)
        if grade > limit:
            warns += 1
            findings.append(("readability",
                             f"Flesch-Kincaid grade {grade} above the body target of {limit}",
                             "WARN", 1, f"grade {grade}"))

    return {"t": t, "grade": grade, "words": words, "findings": findings,
            "fails": fails, "warns": warns, "quote_lines": quote_lines,
            "active": len(active)}


def band_status(cfg, register):
    bs = cfg["band_sets"].get(register)
    if bs:
        p = bs["provenance"]
        label = (f"CALIBRATED '{register}': {p['words']:,} words from "
                 f"{p['files']} file(s), measured {p['date']}")
        return {k: tuple(v) for k, v in bs["bands"].items()}, bs.get("min_words", {}), label, True
    return GENERIC_BANDS, generic_min_words(), \
        f"UNCALIBRATED generic defaults ('{register}' not calibrated)", False


def report(res, cfg, house, args, blabel):
    if args.strip_quotes:
        print(f"NOTE: --strip-quotes removed {res['quote_lines']} blockquote line(s) before scoring.")
        print("      Quoted primary sources are evidence, not your prose.\n")
    n_over = cfg.get("override_count", 0)
    print(f"humanist {__version__}  |  {res['words']:,} words, markdown-stripped")
    print(f"  config      {cfg['path'] if cfg.get('loaded') else 'none loaded (built-in defaults)'}")
    print(f"  rules       {res['active']} active of {len(CHECKS)} shipped"
          + (f", {n_over} overridden" if n_over else "")
          + (", --lenient in effect" if getattr(args, "lenient", False) else ""))
    print(f"  exemptions  {len(house.get('exempt_patterns', []))} pattern(s), "
          f"{len(house.get('never_flag_words', []))} never-flag word(s)")
    print(f"  readability FK grade {res['grade']} (heuristic syllables); targets "
          f"<={house['fk_quotable']} quotable, <={house['fk_body']} body")
    print(f"  bands       {blabel}")
    print()
    if not res["findings"]:
        print("  no findings")
    order = {"FAIL": 0, "WARN": 1, "note": 2}
    for rid, name, sev, n, ex in sorted(res["findings"],
                                        key=lambda f: (order.get(f[2], 3), -f[3])):
        print(f"  {sev:5s}  {name} [{rid}]: {n}  e.g. {ex!r}")


def report_post(res, cfg, register):
    bands, min_words, label, calibrated = band_status(cfg, register)
    s = post_stats(res["t"], cfg["markers"])
    if not s:
        print("\n--mode post: no words to measure.")
        return
    n = s["nwords"]
    print(f"\n--mode post - {label}")
    if calibrated:
        p = cfg["band_sets"][register]["provenance"]
        srcs = ", ".join(p["sources"][:3]) + ("..." if p["files"] > 3 else "")
        print(f"Provenance: your own writing ({srcs}), {p['words']:,} words, {p['date']}.")
    else:
        print("These are wide sanity ranges, nobody's voice. Calibrate on your own")
        print("published writing:  python humanist.py --calibrate <dir>")
    print(f"Sample: {n:,} words.")
    off = untested = 0
    for k, (lo, hi, desc) in bands.items():
        if k not in s:
            continue
        need = min_words.get(k) or 0
        if n < need:
            untested += 1
            print(f"  n/a  {k:9}{s[k]:7.1f}  UNTESTABLE below {need:,}w  ({desc})")
            continue
        v = s[k]
        ok = lo <= v <= hi
        if not ok:
            off += 1
        print(f"  {'ok  ' if ok else 'OFF '}{k:9}{v:7.1f}  band {lo}-{hi}  ({desc})")
    print(f"  {off} marker(s) outside band. {untested} UNTESTABLE at this length.")


MANUAL_TAIL = ("MANUAL checks still owed, because no honest regex catches them: dead "
               "metaphor, fractal summaries, analogy stacking, one-point dilution, "
               "near-verbatim repetition.")

# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------
SLOP_FIXTURE = """Let's dive in and delve into how this seamless audio guide can leverage your museum visit.

It's not just a headset, it's a paradigm shift. Experts agree that this will change everything.

The result? A vibrant ecosystem that reshapes how visitors move.

The key point is that studies show adoption is unstoppable. It's worth noting that the data are clear.

In conclusion, imagine a world where every exhibit narrates itself.
"""

# Every form ai-tropes.md prints for the negative-parallelism family. The previous
# version's rule missed three of these while claiming in its own name to catch
# "every form", so they are fixtures now.
NEG_PARALLEL_FIXTURES = [
    ("inline uncontracted", "It's not a warehouse, it's a service."),
    ("inline contracted", "This isn't about temperature, it's about pressure."),
    ("sentence-split past", "That is not what cracked the glaze. What cracked it was a kiln cooling too fast."),
    ("sentence-split contracted", "It's not a warehouse. It's a service."),
    ("negated appositive", "That is a guess, not a measurement."),
    ("scaled", "This is not just a delay, but a design failure."),
]

CLEAN_FIXTURE = """I reprinted the contact sheet on Tuesday. It came out muddy twice before I found the light leak in the enlarger head. The fix took ten minutes of black tape.

We timed the wash cycle before and after: 14 minutes down to 9 in the same sink. My colleague repeated the timing on Friday and got 10.

If the developer runs cold, each print adds about 90 seconds. That cost shows up on the first batch of every session.
"""

CURLY_FIXTURE = "It’s worth noting that here’s the thing: let’s dive in.\n"
BOM_FIXTURE = "﻿## Why we did it because it was cheaper\n\nSome body text follows here.\n"
ARROW_FIXTURE = "The pipeline goes A → B and ≤ that is all it does today.\n"


def selftest():
    house = dict(HOUSE_CONFIG)
    state = {"ok": True}

    def check(label, cond, detail=""):
        state["ok"] = state["ok"] and bool(cond)
        suffix = f"  {detail}" if detail and not cond else ""
        print(f"  {'PASS' if cond else 'FAIL'}: {label}{suffix}")

    print("SELFTEST")
    slop = analyze(SLOP_FIXTURE, house)
    ids = {rid for rid, _, sev, _, _ in slop["findings"] if sev == "FAIL"}
    allids = {rid for rid, _, _, _, _ in slop["findings"]}
    for want in ("drama-question", "verdict-preamble", "vague-attribution",
                 "signposted-conclusion", "break-it-down"):
        check(f"slop fixture fails [{want}]", want in ids, f"got {sorted(ids)}")
    for want in ("ai-vocab", "neg-parallel"):
        check(f"slop fixture flags [{want}]", want in allids, f"got {sorted(allids)}")
    check("slop fails 5 or more distinct rules", len(ids) >= 5, f"got {len(ids)}")

    # Detection, not severity. These six forms are what the rule's own name
    # claims to catch and three of them used to be unreachable; the rule reports
    # WARN because the corpus showed the FAIL was not defensible, but it must
    # still SEE all six.
    for label, text in NEG_PARALLEL_FIXTURES:
        r = analyze(text, house)
        hit = any(rid == "neg-parallel" for rid, _, _, _, _ in r["findings"])
        check(f"neg-parallel catches the {label} form", hit, repr(text))

    # The corpus false positives that drove the two demotions. These must stay
    # clear of FAIL, or the demotions have silently been undone.
    for label, text in [
        ("Strunk's correlative not-only", "This is true not only in narrative principally concerned with action, but in writing of any kind."),
        ("literal foster care", "In 2009, DeBoer and Rowse fostered and then adopted a baby boy."),
        ("literal crucial", "It is clear that crucial information about the O-ring damage was withheld."),
        ("literal utilize", "The procedures to establish connections utilize the synchronize control flag."),
    ]:
        r = analyze(text, house)
        bad = [rid for rid, _, sev, _, _ in r["findings"] if sev == "FAIL"]
        check(f"human prose does not FAIL: {label}", not bad, f"FAILed on {bad}")

    curled = analyze(CURLY_FIXTURE, house)
    cids = {rid for rid, _, sev, _, _ in curled["findings"] if sev == "FAIL"}
    check("curly apostrophes do not blind the rules",
          {"worth-noting", "kicker", "break-it-down"} <= cids, f"got {sorted(cids)}")
    check("the curly-quote rule still sees curly quotes",
          any(rid == "curly-quotes" for rid, _, _, _, _ in curled["findings"]))

    bom = analyze(BOM_FIXTURE, house)
    bids = {rid for rid, _, _, _, _ in bom["findings"]}
    check("a leading BOM does not disable line-anchored rules",
          "self-justifying-heading" in bids, f"got {sorted(bids)}")

    try:
        arrow = analyze(ARROW_FIXTURE, house)
        report(arrow, {"path": "none", "loaded": False, "override_count": 0}, house,
               argparse.Namespace(strip_quotes=False, lenient=False), "n/a")
        check("reporting a unicode-arrow finding does not crash", True)
    except UnicodeEncodeError as e:
        check("reporting a unicode-arrow finding does not crash", False, str(e))

    typo = analyze("A line — with an em dash and “curly quotes” here.\n", house)
    sevs = {rid: sev for rid, _, sev, _, _ in typo["findings"]}
    check("em dash defaults to WARN, not FAIL", sevs.get("em-dash") == "WARN", str(sevs))
    check("curly quotes default to WARN, not FAIL", sevs.get("curly-quotes") == "WARN", str(sevs))

    clean = analyze(CLEAN_FIXTURE, house)
    check("clean fixture has 0 FAIL", clean["fails"] == 0,
          f"{clean['fails']} FAIL: {[f[1] for f in clean['findings'] if f[2] == 'FAIL']}")

    print(f"SELFTEST {'PASSED' if state['ok'] else 'FAILED'}.")
    sys.exit(EXIT_CLEAN if state["ok"] else EXIT_FAILS)


# ---------------------------------------------------------------------------
def parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="humanist.py",
        description="Mechanical prose sweep for AI writing tells. It reports; it never edits.")
    ap.add_argument("draft", nargs="?", help="prose draft (.md/.txt) to sweep")
    ap.add_argument("--strip-quotes", action="store_true",
                    help="drop blockquote lines before scoring (quoted sources are evidence, not your prose)")
    ap.add_argument("--lenient", action="store_true",
                    help="downgrade format and phrasing rules to notes (internal-doc register)")
    ap.add_argument("--mode", choices=["post"], help="also report register-band stats")
    ap.add_argument("--register", default="default", help="named band set to check against or calibrate")
    ap.add_argument("--calibrate", metavar="DIR", help="measure bands from a directory of YOUR OWN writing")
    ap.add_argument("--config", metavar="PATH",
                    help=f"config file (default: ./{CONFIG_NAME}, then beside this script)")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON on stdout")
    ap.add_argument("--rules", action="store_true", help="list every rule ID, severity and register, then exit")
    ap.add_argument("--selftest", action="store_true", help="run embedded fixtures; exit 0 only if all behave")
    ap.add_argument("--version", action="version", version=f"humanist {__version__}")
    return ap.parse_args(argv)


def print_rules():
    print(f"{'ID':26} {'SEV':5} {'REGISTER':10} NAME")
    for rid, name, sev, _, _, reg in CHECKS:
        print(f"{rid:26} {sev:5} {reg:10} {name}")
    print(f"\n{len(CHECKS)} rules. severity_overrides keys must match an ID exactly.")
    print("--lenient downgrades FAIL rules in the format and phrasing registers to notes.")


def main(argv=None):
    _reconfigure_streams()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        selftest()
        return
    if args.rules:
        print_rules()
        return
    cfg = load_config(default_config_path(args.config))
    if args.calibrate:
        calibrate(args.calibrate, args.register, cfg)
        return
    if not args.draft:
        print("usage: humanist.py <draft.md> [options]   (--help for the full list)",
              file=sys.stderr)
        sys.exit(EXIT_ERROR)

    raw = read_text(args.draft, "draft")
    res = analyze(raw, cfg["house"], lenient=args.lenient, strip_quotes=args.strip_quotes)
    _, _, blabel, _ = band_status(cfg, args.register)

    if args.json:
        print(json.dumps({
            "version": __version__, "file": args.draft, "words": res["words"],
            "fk_grade": res["grade"], "fails": res["fails"], "warns": res["warns"],
            "config": cfg["path"] if cfg["loaded"] else None,
            "rules_active": res["active"], "rules_shipped": len(CHECKS),
            "findings": [{"id": r, "name": n, "severity": s, "count": c, "example": e}
                         for r, n, s, c, e in res["findings"]],
        }, indent=1))
    else:
        report(res, cfg, cfg["house"], args, blabel)
        if args.mode == "post":
            report_post(res, cfg, args.register)
        print(f"\nRESULT: {res['fails']} FAIL, {res['warns']} WARN. "
              f"{'CLEAN.' if res['fails'] == 0 else 'Fix the FAILs before shipping.'}")
        print(MANUAL_TAIL)

    sys.exit(EXIT_CLEAN if res["fails"] == 0 else EXIT_FAILS)


if __name__ == "__main__":
    main()
