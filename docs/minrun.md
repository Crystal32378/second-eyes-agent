# Min-run wiring (branch `runtime/min-wiring`, doc + code, no model calls)

Chain: `briefs/brief-v1.json` → `fixtures/minrun/observations.json`
(fixed, staged refs) → `agent.loop.route` → `runtime/brief_gate.gate`
→ results JSON. Counts come from results, never 18/7/375.
Public `ui/workroom/` pages are untouched; the preview lives in
`ui/minrun/` (outside the Pages artifact path).

## Operate (from repo root, no credentials needed)

```bash
python3 -m unittest discover -s tests -v   # 15/15 existing + new gate tests
python3 runtime/run_min.py --brief briefs/brief-v1.json \
  --obs fixtures/minrun/observations.json --out outputs/minrun.json \
  --emit-preview ui/minrun/preview.html
python3 runtime/run_min.py --no-brief \
  --obs fixtures/minrun/observations.json --out outputs/minrun-nobrief.json
python3 -m http.server 8123   # then open ui/minrun/results.html with
                              # outputs/minrun.json copied next to it as results.json,
                              # or just open ui/minrun/preview.html directly
```

## Expected model calls

- This branch: **0**. All tests and pipeline runs use fixed observations;
  `results["model_calls"]` is 0 by construction.
- Next gate (real small-set test, NOT run here):
  `fixtures/smallset/manifest.json` stages 6 approved derivatives
  (BACK-5F20, IG-262, IG-277, IMG-4489, ROBE-5059, WEAR-8106).
  Expected volume: **6 image calls** (1 per photo, fresh agent each,
  image-only) + optionally 1 text-only connectivity check = **6–7 calls**.
  Video is out of scope (`BLOCKED_UNSUPPORTED`).
