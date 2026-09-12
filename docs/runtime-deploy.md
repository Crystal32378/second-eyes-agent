# Runtime viewer deploy plan (준비 only — NOT deployed)

Status: branch artifact, reviewed locally. No merge to main, no Amplify
deployment, no Pages change has been made from this branch.

## What goes live (and what does not)

- LIVE: `ui/runtime/` (index.html, results.json, styles.css, assets/×6)
  plus the one-line neutral nav link added to the two workroom pages.
- NOT live: `outputs/`, `fixtures-driving` internals, raw responses,
  usage metadata, `ui/minrun/` sketches. None of these are in the package.
- 400-photo page = publishing scenario / presentation layer (mock counts
  18 / 7 / 375, illustrative, untouched in meaning).
- 6-image page = verified small-set runtime (computed 1 / 2 / 3).
  Counts are never combined. Neither page claims legal clearance or
  accuracy proof.

## Package (exact, reproducible)

Mirror layout — the zip preserves the repo `ui/` structure so every
relative link works identically in review and in production:

```bash
cd ui && rm -f /tmp/amplify-second-eyes.zip \
  && zip -r /tmp/amplify-second-eyes.zip workroom runtime \
  -x '*/.DS_Store' 'workroom/assets/.DS_Store'
unzip -l /tmp/amplify-second-eyes.zip
```

Expected content: `workroom/brief-established.html`,
`workroom/brief-missing.html`, `workroom/index.html`,
`workroom/styles.css`, `workroom/assets/×12`, `runtime/index.html`,
`runtime/results.json`, `runtime/styles.css`, `runtime/assets/×6`.

## Deploy checklist (separate preview first)

1. Deploy the zip to a NEW Amplify app (or a preview branch), never
   over the existing workroom deployment.
2. Verify (record URLs + timestamps in the Fu thread):
   - `/runtime/` renders 1 Shortlist · 2 Needs Review · 3 Remaining.
   - Hero / Product — HAVE (ROBE-5059); Detail — MISSING, not guessed.
   - All 6 photos load; no console errors; 390px width single column.
   - Workroom pages show "03 View verified 6-image runtime" and reach
     `/runtime/`; the runtime page links back to the 400-photo scenario.
   - ` /runtime/results.json` contains no raw/usage/credentials/private
     paths (re-run `runtime/export_public.py` audit + test suite).
3. Only after Fu visual + content sign-off: decide whether the main
   Amplify app also serves `/runtime/`; existing root URLs
   (`/brief-established.html`) must keep working.
4. Rollback: delete the preview app. Nothing else changes.

## Verification evidence on this branch

- `docs/qa/runtime-desktop.png` (1440px) and `docs/qa/runtime-mobile.png`
  (390px), rendered by headless Chrome over local http with zero page
  errors (see commit).
- `tests/test_export_public.py`: mechanical derivation, sanitization,
  byte-exact images, bidirectional links, mock counts intact (83+ tests
  green with the full suite).
