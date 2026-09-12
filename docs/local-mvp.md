# Local MVP (branch `mvp/local-wiring`, no model calls, no merge/deploy)

Three checkpoints, one branch, tests green before each next step:
- C1: editor-declared signals (`fixtures/smallset/signals.json`,
  `runtime/signals.py`). `long_edge` forbidden in file (measured).
- C2: sealed-input pipeline (`runtime/local_mvp.py`) with computed
  coverage. Sealed SHA verified before every run; route recomputed and
  must equal sealed evidence; manifest verified; results carry sealed
  raw/usage/model plus manifest, `stubbed` flags, summary, coverage.
- C3: live-data viewer (`ui/minrun/local.html` + inlined preview).
  Public `ui/workroom/` untouched.

## Operate (from repo root, copy-paste as one block)

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python runtime/local_mvp.py --out outputs/local-mvp.json \
  --emit-preview ui/minrun/preview-local.html
cp outputs/local-mvp.json ui/minrun/local-mvp.json
.venv/bin/python -c "import json; d=json.load(open('outputs/local-mvp.json')); print(d['summary'], d['coverage'])"
python3 -m http.server 8123
```

Then open `http://localhost:8123/ui/minrun/local.html`
(reads同目錄 `local-mvp.json`), or open
`ui/minrun/preview-local.html` directly over file://.

`outputs/local-mvp.json`, `ui/minrun/local-mvp.json`,
`ui/minrun/preview-local.html` are git-ignored local artifacts.
The sealed model-gate file is read-only input and is never rewritten
(verify: `sha256sum outputs/smallset-gate_20260912T094617Z.json`
must equal the receipt in `docs/model-gate.md`).

## Data honesty

`signals.json` stub sources (`editor:mvp-stub`) are wiring placeholders
for this local demo only and MUST be replaced by editor-verified facts
before any real use. Items decided on consulted stub signals carry
`stubbed:true` and a STUB badge in both viewers. has_people cites
`docs/demo-derivatives.md` where stated; unknown stays null and stops
at Needs Review instead of guessing.

## Final-gate blockers (Fu ruling, enforced in results)

- Any `stubbed:true` Shortlist sets `summary.public_ready: false`.
  Such output must NOT feed the public workroom and must NOT be
  deployed. Before the final gate, either replace stubs with
  editor-verified facts or keep the whole batch clearly marked
  LOCAL/STUB.
- `check_sealed_binding` pins sealed evidence to the current manifest
  per item (asset_key/path/sha256/ref_convention + old expansion).
  A same-key file swap that `verify_manifest` alone would accept is
  rejected here with exit 2 and zero output.
- UI visual acceptance remains BLOCKED: HTML string tests verify
  wiring only, never visual correctness.
