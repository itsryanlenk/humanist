---
name: Bug report
about: Something crashed, hung, or did the wrong thing
title: ""
labels: bug
---

<!-- For a rule that fired on good English, use the "False positive" template
     instead — it asks for the right things. -->

## What happened

## What you expected instead

## Reproduction

```
the exact command you ran
```

```
the exact output, including any traceback, in full
```

## The input

<!-- If you can attach or paste the file that triggered it, do. If the content is
     private, a reduced version that still reproduces the problem is just as good
     — and often more useful, since it isolates the cause. -->

## Environment

- Which tool: [ ] the checker (`humanist.py`) [ ] `html2prose.py` [ ] Inkwash (`app/inkwash.html`)
- OS and version:
- Python version (`python --version`):
- Browser and version (Inkwash only):
- Line endings in the input file, if you know: [ ] LF [ ] CRLF [ ] not sure
- Is there a `humanist.config.json` in your working directory? [ ] yes [ ] no

<!-- That last pair matters more than it sounds. The checker is line-oriented in
     several places, and it silently auto-loads a config from the current
     directory, so both can change the result without appearing in your command. -->
