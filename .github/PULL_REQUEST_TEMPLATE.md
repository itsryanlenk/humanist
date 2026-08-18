## What this changes

<!-- One or two sentences. What is different after this merges? -->

## Which kind of change is it?

- [ ] **Implementation fix** — a rule did not match its own stated law, and now it
      does. The law is unchanged.
- [ ] **Rule change** — the law itself is different now. Say what it used to be and
      what it is now, and why the old one was wrong.
- [ ] New rule
- [ ] Documentation
- [ ] Inkwash (the app)
- [ ] Tooling, CI, or repo plumbing

That first distinction is load-bearing. Widening a regex so it matches the law it
already claimed to enforce is maintenance. Changing the law is a decision, and it
needs the reasoning written down.

## Evidence

<!-- Paste real output. Not a description of output. -->

- [ ] `python scripts/validate_repo.py` passes
- [ ] `python -m unittest discover -s tests` passes
- [ ] `python tests/fp_guard.py` passes — **and the false-positive rate did not go up**
- [ ] `node app/test-inkwash.mjs` passes (if Inkwash changed)

### For a new or changed rule, additionally:

- [ ] A true positive it must catch, added to the fixtures
- [ ] A piece of ordinary, well-written human English it must **not** catch, added
      to the fixtures
- [ ] The false-positive corpus was re-swept and the delta is stated below

```
paste the before/after FAIL-per-1000-words figures here
```

## Anything you are unsure about

<!-- Genuinely useful. A reviewer would rather know where you were uncertain than
     discover it themselves. -->
