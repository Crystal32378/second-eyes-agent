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

## GitHub Pages package (what actually deploys)

`.github/workflows/pages.yml` publishes an artifact staged by
`tools/build_pages.py`, not the raw `ui/workroom` directory:

```
_site/
  index.html                 <- existing root URL, unchanged
  brief-established.html
  brief-missing.html
  styles.css
  assets/ x12
  runtime/
    index.html               <- /runtime/
    results.json
    styles.css
    assets/ x6
```

The repo keeps the two pages as siblings (`ui/workroom`, `ui/runtime`),
so they cross-link with `../`. The site keeps the workroom at the root
URL, which puts the two at different depths. `tools/build_pages.py`
rewrites exactly those cross-links from an explicit table
(`../runtime/` -> `runtime/`, `../workroom/x` -> `../x`), then resolves
every local `href`/`src`/meta-refresh in the staged tree against the
staged files and refuses to publish on any miss. An `../` reference that
is not in the rewrite table stops the build rather than 404-ing only in
production.

Build and inspect locally:

```bash
python3 tools/build_pages.py --out _site --print-manifest
```

The workflow triggers on `ui/workroom/**`, `ui/runtime/**`,
`tools/build_pages.py`, and the workflow file itself, so a runtime-only
change now deploys (before this branch it did not).

## Amplify package (alternative, unchanged)

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
   - Workroom pages show "03 View recorded 6-image run" and reach
     `/runtime/`; the runtime page links back to the 400-photo scenario.
   - ` /runtime/results.json` contains no raw/usage/credentials/private
     paths (re-run `runtime/export_public.py` audit + test suite).
3. Only after Fu visual + content sign-off: decide whether the main
   Amplify app also serves `/runtime/`; existing root URLs
   (`/brief-established.html`) must keep working.
4. Rollback: delete the preview app. Nothing else changes.

## Verification evidence on this branch

- `docs/qa/runtime-desktop.png` (1440px), `docs/qa/runtime-mobile.png`
  (390px) and `docs/qa/workroom-mobile.png` (390px), rendered by headless
  Chromium over local http against the STAGED Pages artifact, with zero
  page errors.
- 390px horizontal overflow: measured `document.documentElement.scrollWidth`
  vs `clientWidth` on all four pages at 390x844 and 1440x900, in both the
  repo layout and the staged artifact. Before: workroom pages 398 vs 390
  (the three-link preview nav, `white-space:nowrap`). After: 390 vs 390
  everywhere, no element extending past the viewport.
- `tests/test_export_public.py`: mechanical derivation, sanitization,
  byte-exact images, bidirectional links, mock counts intact.
- `tests/test_export_lineage.py`: the published bundle is recomputed from
  the sealed input; a tampered `outputs/local-mvp.json` (summary, bucket,
  coverage, verdict, public_ready, corrupt JSON) stops the export and
  leaves `ui/runtime/` byte-identical.
- `tests/test_pages_build.py`: artifact layout, cross-link rewrites, and
  a negative case proving the link checker fails on a broken link.
- `tests/test_viewer_copy.py`: no live-runtime claim, banner wording,
  static-viewer statement, and the 390px nav-wrap rule.
