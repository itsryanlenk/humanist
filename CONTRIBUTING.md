# Contributing

## The one rule that matters

**A rule change and an implementation fix are different things, and they carry
different burdens.**

Widening a regex so that it finally matches the law it already claimed to enforce
is an _implementation fix_. It needs a test and a re-sweep, and that is all.

Changing what the law says is a _decision_. It needs the old law, the new law, and
the argument for why the old one was wrong — written down in the pull request, not
in a commit message that nobody will find again.

Both get swept over the false-positive corpus before they land. Neither gets to
skip that.

## The second rule

**Every new rule needs a negative fixture.** Not "here is prose it catches" — that
part is easy and everyone remembers it. The required part is a piece of ordinary,
well-written human English that the rule must **not** fire on, committed alongside
it.

This exists because the project's own first audit measured the shipped rule set
against 107,191 words of published human prose from 1854 to 2018 and found that
**91.7% of those documents would have been blocked**, with 94.6% of the failures
coming from two typography rules. A checker that fails nine of ten published
essays is not measuring what it claims to measure. The negative fixture is how
that stays fixed.

## Setup

Python 3.9 or newer, standard library only. Node 18+ only if you are touching
Inkwash. Nothing to install.

```bash
git clone https://github.com/itsryanlenk/humanist
cd humanist
python scripts/validate_repo.py
```

## Before you open a pull request

```bash
python scripts/validate_repo.py                      # structure, manifests, references, privacy
python -m unittest discover -s tests                 # the regression suite
python tests/fp_guard.py                             # the false-positive ceiling
node app/test-inkwash.mjs                            # only if Inkwash changed
```

Paste the real output into the pull request. A description of output is not output.

## The privacy gate

`scripts/validate_repo.py` fails the build on absolute home paths, email addresses,
local temp paths, key material and tokens. This is not bureaucracy — the repository
is meant to be handed to anyone, and one leaked absolute home path in a doc makes it
obvious it was not. If you hit the gate, generalize the path rather than adding an
exception. Exceptions live in `PRIVACY_ALLOW` and each one has to carry its reason.

**Shipped patterns describe the shape of a leak, never the identity of a person.**
If you want the gate to also catch your own username, handles, or the names of
unrelated private repos you work in, put them one per line in `.privacy-terms`,
which is gitignored. Do not add them to `PRIVACY_PATTERNS`, and do not put them in a
comment either.

The rule is easy to get backwards, so it is worth stating plainly: **a denylist of
secrets is a disclosure of secrets.** A committed list of the names you want kept
private is a greppable inventory of exactly those names, and usually a stronger
identity link than any of the file paths the gate was built to catch.

## Proposing a new tell

Open a rule proposal issue first. Bring three things:

1. **At least three real examples**, from prose you did not write for the occasion.
   Invented examples always confirm the rule that invented them.
2. **A near-miss** — the closest legitimate construction the rule must not catch.
3. **A severity argument.** FAIL means it never ships in public copy. That is a
   strong claim about a piece of English, and most candidates are WARN.

Rules that ban a common English word outright are house taste, not universal law,
and belong in a user's own config rather than the shipped set.

## Reporting a false positive

This is the most valuable kind of issue this project receives, and there is a
template for it. Bring the sentence, the rule that fired, and why the sentence is
fine. If it is fine, the rule is wrong — not your prose.

## Style

Match the file you are editing. The Python is stdlib-only, terse, and heavily
commented where a decision is non-obvious; keep it that way. The prose in this
repository is subject to its own checker, which is either fitting or unbearable
depending on the day.
