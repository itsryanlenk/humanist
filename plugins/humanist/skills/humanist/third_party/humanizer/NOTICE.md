# Third-party notice

## humanizer

Vendored from <https://github.com/blader/humanizer> v2.8.0.

Copyright (c) 2025 Siqi Chen. Licensed under the MIT License; the full text is in
`LICENSE` beside this file, byte-identical to upstream (sha256
`4ac4810254ab36d45419141aeb8e69bf50652cfafe5b2dab947d06d44e5cbf96`).

### Modifications

One change, recorded here as MIT requires: the YAML frontmatter has been removed
from `SKILL.md`, so that a plugin loader treats this file as documentation rather
than registering it as a second, independently-triggering skill. No pattern
content was altered.

### Additional license on part of this work

The pattern catalog in `SKILL.md` is substantially derived from Wikipedia's
[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
maintained by WikiProject AI Cleanup. Upstream's changelog for v2.0.0 states:
_"Complete rewrite based on raw Wikipedia article content."_

Measured against the Wikipedia revision immediately preceding that rewrite:
**618 words across 51 maximal verbatim runs of six or more words, being 27.5% of
the operative pattern catalog.** What was taken is Wikipedia's selection of
examples, its watch-word lists in their original order, its problem statements and
its section taxonomy. The "After:" rewrites are original to the humanizer and
produced zero matches.

Wikipedia's text is licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). ShareAlike
requires that adaptations be distributed under CC BY-SA 4.0 or a compatible
license. MIT is not compatible, because MIT permits downstream relicensing with no
copyleft carry-forward, which is exactly what ShareAlike forbids.

**Therefore: the pattern catalog in `SKILL.md` is available under CC BY-SA 4.0, not
under this repository's MIT grant.** If you copy that material onward, CC BY-SA 4.0
travels with it. The rest of the repository is MIT.

See `docs/attribution.md` at the repository root for the full inventory, the
measurement method, and the per-section overlap table.
