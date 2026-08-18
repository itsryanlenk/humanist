---
name: Rule proposal
about: Propose a new tell for the checker to catch
title: "Rule: <the construction>"
labels: rule-proposal
---

## The construction

<!-- Name it and describe the shape. -->

## Three real examples

<!-- From prose you did not write for this issue. Invented examples always confirm
     the rule that invented them, which is why three found ones are worth more than
     ten made-up ones. Link the source where you can. -->

1.
2.
3.

## The near-miss it must NOT catch

<!-- The closest legitimate construction. Every rule in this checker has one, and
     the ones that shipped without it are the ones that later turned out to fire on
     ordinary writing. -->

## Proposed severity

- [ ] **FAIL** — this never ships in public copy
- [ ] **WARN** — judge in context, but count it so repetition stays visible

<!-- FAIL is a strong claim about a piece of English. Most candidates are WARN.
     If the construction is fine once and only a tell when repeated, it is a WARN. -->

## Why the alternative is better

<!-- What should the writer do instead? A rule that flags without an alternative
     just makes people delete the sentence and lose the point it was making. -->

## Is this house taste or universal?

<!-- A ban on a common English word is almost always house taste and belongs in a
     user's own config rather than the shipped rule set. Be honest here; it is not
     a lesser outcome, and the config mechanism exists precisely for this. -->

## Does the rewrite pass already handle it?

<!-- Check `plugins/humanist/skills/humanist/third_party/humanizer/SKILL.md`
     first. If the rewrite pass already
     removes the construction, a checker rule may be redundant — or, worse, may
     fire on the output the rewrite pass produces. Both have happened. -->
