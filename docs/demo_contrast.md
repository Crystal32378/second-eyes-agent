# Demo contrast rule (from review — mandatory for video)

UNKNOWN and CONFLICT look identical to "broken" on screen. Every such case
in the demo MUST be shown side-by-side:

- UNKNOWN: left = what a generic auto-tagger would assert
  (e.g. `beige, product shot`); right = ours
  (`UNKNOWN — 只看到裁切後的織物,無法判定顏色或品項`).
  The avoided error is the achievement, not the empty result.
- CONFLICT: old label vs observed evidence, two sentences side-by-side.
  Never show an empty/ask-human cell without its contrast.

Synthetic fixtures prove plumbing only (loop runs, routing branches,
logging complete). The only citable accuracy evidence is the Batch A 60
blind run — that is the number allowed in the demo.
