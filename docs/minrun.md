# Min-run wiring (branch `runtime/min-wiring`, doc + code, no model calls)

Chain: `briefs/brief-v1.json` → `fixtures/minrun/observations.json`
(fixed, staged refs) → `agent.loop.route` → `runtime/brief_gate.gate`
→ results JSON. Counts come from results, never 18/7/375.
Public `ui/workroom/` pages are untouched; the preview lives in
`ui/minrun/` (outside the Pages artifact path).

## Operate (from repo root, no credentials needed)

Full sequence, copy-paste as one block. It runs tests, regenerates both
result files, wires `minrun.json` to the file the viewer reads
(`ui/minrun/results.json`), emits the file:// preview, then serves:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python runtime/run_min.py --brief briefs/brief-v1.json \
  --obs fixtures/minrun/observations.json --out outputs/minrun.json
.venv/bin/python runtime/run_min.py --no-brief \
  --obs fixtures/minrun/observations.json --out outputs/minrun-nobrief.json
cp outputs/minrun.json ui/minrun/results.json
.venv/bin/python runtime/run_min.py --brief briefs/brief-v1.json \
  --obs fixtures/minrun/observations.json --out outputs/minrun.json \
  --emit-preview ui/minrun/preview.html
.venv/bin/python -c "import json; print(json.load(open('outputs/minrun.json'))['summary'])"
python3 -m http.server 8123
```

Then open (served, so `fetch("results.json")` works):
- `http://localhost:8123/ui/minrun/results.html` (reads同目錄 `results.json`)
- or open `ui/minrun/preview.html` directly over file:// (counts inlined).

`outputs/*.json`, `ui/minrun/results.json`, `ui/minrun/preview.html`
are git-ignored local artifacts; they stay on disk for acceptance and
are never committed. Only `ui/minrun/results.html` (the viewer source)
is tracked.

## Guarantees added for acceptance

- `has_people` is tri-state under `no_people=true`: `true` → 明確不符
  (Remaining); missing/`null` → 證據不足 (Needs Review); non-boolean →
  資料錯誤 (Needs Review, never passes).
- Results keep per-item `observed` (values + refs), `signals`, and
  `signal_sources`; both viewer pages render them. Fixed inputs are
  marked `"fixture": true` from `fixtures/minrun/observations.json`
  through to each result item.
- Real-image runs must pass `--manifest fixtures/smallset/manifest.json`
  first: asset presence, sha256, and `ref_convention` are verified and
  any mismatch aborts (exit 2) before any model call could happen.
- Custody binding (`runtime/smallset.py::check_binding`, enforced by
  `--manifest`): manifest asset_keys and observation asset_keys must
  match exactly with equal counts — missing, extra, or duplicate keys
  abort with exit 2 and nothing is written. `fixture:true`
  observations are rejected in real mode. Every attached observation
  ref must start with the manifest's `ref_convention`; each result
  keeps its manifest `{path, sha256, ref_convention}`. Both viewers
  render it.

## Expected model calls

- This branch: **0**. All tests and pipeline runs use fixed observations;
  `results["model_calls"]` is 0 by construction.
- Next gate (real small-set test, NOT run here):
  `fixtures/smallset/manifest.json` stages 6 approved derivatives
  (BACK-5F20, IG-262, IG-277, IMG-4489, ROBE-5059, WEAR-8106).
  Expected volume: **6 image calls** (1 per photo, fresh agent each,
  image-only) + optionally 1 text-only connectivity check = **6–7 calls**.
  Video is out of scope (`BLOCKED_UNSUPPORTED`).
