# Demo contrast rule (from review — mandatory for video)

UNKNOWN and CONFLICT look identical to "broken" on screen. Every such case
in the demo MUST be shown side-by-side:

- UNKNOWN: left = what a generic auto-tagger would assert
  (e.g. `beige, product shot` — ILLUSTRATIVE failure mode, not a measured
  baseline unless one is actually run); right = ours
  (`UNKNOWN — 只看到裁切後的織物,無法判定顏色或品項`).
  The avoided error is the achievement, not the empty result.
- CONFLICT: old label vs observed evidence, two sentences side-by-side.
  Never show an empty/ask-human cell without its contrast.

Synthetic fixtures prove plumbing only (loop runs, routing branches,
logging complete). Batch A reports routing distribution and evidence
coverage only, not accuracy — those are the only numbers allowed in
the demo.

## Evaluation claim rule: NO accuracy claims

`observations.jsonl` is a single-model record (96/132 without cross-check,
at least one description known to mismatch its asset). Any number computed
against it is "agreement with Mini", not accuracy —拆得動, so we never
put it in a public submission as accuracy.

Report instead (needs only run logs, no answer key):
  60 筆:自動歸檔 N、送人判 M、證據不足退回 K。
  全程沒有任何一句斷言是它拿不出證據的。
That IS the differentiator. A Crystal spot-checked subset is an optional
bonus, never the foundation of the claim.
