# Security Policy

## Reporting a vulnerability

Use this repository's [private vulnerability reporting form](../../security/advisories/new).
It is confidential and visible only to the maintainers. Please do not open a public
issue for a security problem.

Include what you sent in, what happened, and what you expected. A file that
reproduces the problem is worth more than a description of it.

## What this project is, for threat-modeling purposes

Two local, offline tools. Neither makes a network request, and neither has any
dependency beyond the Python standard library and a browser.

- **The checker** (`humanist.py`) is a command-line program that reads three kinds
  of untrusted input: a prose draft, an HTML body export, and a JSON configuration
  file. It writes exactly one file, and only when `--calibrate` is used.
- **Inkwash's document import** parses untrusted `.docx` files with a hand-written
  ZIP reader. It inflates only the four entries a `.docx` keeps prose and metadata
  in, and it aborts on any entry over 32 MB or any archive over 64 MB inflated, so a
  decompression bomb is refused rather than expanded. Findings here are in scope, and
  a malformed archive that hangs or crashes the tab is worth reporting.
- **Inkwash** (`app/inkwash.html`) is a single HTML file that runs entirely in the
  browser. Text pasted into it is never uploaded, stored, or transmitted. There is
  no server, no analytics, and no fetch of any kind — which you can confirm by
  reading the file, because the whole program is in it.

### In scope

- Anything that makes the checker hang, crash, or consume unbounded memory on a
  realistically-sized input. The rule set is regular expressions over user text,
  so catastrophic backtracking is the most likely class of finding here.
- A configuration file that causes arbitrary code execution, an unexpected file
  write, or **silent total suppression of findings**. That last one matters more
  than it looks: a config that makes the checker always report zero while
  appearing normal defeats the entire purpose of the tool, and we treat it as a
  security problem rather than a usability one.
- Anything in `html2prose.py` that lets crafted HTML inject structure into the
  extracted text — a fabricated blockquote or heading changes what the checker
  scores.
- Anything in Inkwash that transmits input off the machine, or that corrupts text
  in a way the report does not disclose.

### Out of scope

- The checker reporting a finding you disagree with. That is a rules question;
  open an issue.
- Claims that the tools fail to defeat a particular AI-detection service. They do
  not attempt this, the documentation says so plainly, and it is not a security
  boundary.
- Anything requiring an attacker who already has write access to your machine.

## A note on the calibration config

`--calibrate` writes `humanist.config.json`, which records the **filenames**,
file count and word count of the corpus it measured, along with the measured
rates. It does not record any of your prose. It is listed in `.gitignore` because
those filenames are still yours, not the repository's.
