# Model gate (branch `model/smallset-gate`, independent of runtime wiring)

Narrow scope, locked: the 6 images in `fixtures/smallset/manifest.json`
only, one fresh agent per photo, image blocks only, zero video.
Locked prompt, frozen vocab, manifest-pointed brief, manifest-injected
old labels, mechanical refs. No prompt/vocab/brief/fixture file is
modified by this gate.

Signals: only `long_edge` is measured from bytes (`bytes:measured`).
Scene/person/channel/SKU are undeclared, so the brief-gate honestly
stops photos at Needs Review on the missing person signal. That stop
IS part of what this gate verifies, together with real observation
plumbing (strict JSON parse → route → gate → results with manifest).

## Operate (from repo root; project via env, ADC otherwise)

```bash
.venv/bin/python -m unittest discover -s tests -v
GOOGLE_CLOUD_PROJECT=<proj> .venv/bin/python runtime/run_smallset_gemini.py
```

## Stop rules

First anomaly stops immediately with a nonzero exit and a diag file
under `outputs/` — no retries, no silent reruns, no prompt/vocab edits:
- exit 2: custody/brief/manifest (sha mismatch, count != 6, video
  entry, unreadable image).
- exit 3: schema (`PROMPT_ISSUE`: non-JSON, wrong shape, out-of-vocab
  token). Raw response is preserved in the diag file.
- exit 4: provider/quota/transport (incl. missing credentials).

## Results (local only, git-ignored)

`outputs/smallset-gate_<stamp>.json`: per item — asset_key,
evidence_state, verdict/bucket/reason/pending/resolver, observed
(values + mechanical refs), injected old, signals + sources, manifest
(path/sha/convention), model, prompt_version, usage, stop_reason,
full raw response. Partial results + diag on stop. Hand the file to
Fu for verification; no merge, no deploy, public workroom untouched.

## Run record — 2026-09-12 (first attempt, no anomalies, no reruns)

- File (local, git-ignored): `outputs/smallset-gate_20260912T094617Z.json`
- `complete: true`, model `gemini-2.5-flash`, prompt `syn-obs-v1`,
  `model_calls: 6`, `fixture: false`. Zero retries.
- Summary: Shortlist 0 / Needs Review 6 / Remaining 0. All six routed
  NEW (manifest old_label "none" injected, as designed) and stopped at
  Needs Review on the missing person signal under `no_people=true` —
  the honest outcome this gate was built to verify.
- Every item: `stop_reason: end_turn`, accumulated token usage recorded
  (~1600–2150 total tokens each), full raw strict-JSON preserved,
  refs exactly `workroom:frame-full`, manifest path/sha attached.
- No schema/quota/provider/custody anomaly encountered. No accuracy
  claimed: selections are observations with refs, pending human review.
