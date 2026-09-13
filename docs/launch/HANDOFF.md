# Second Eyes — Sample Case Mode handoff

Implemented 2026-09-13 on branch `launch/sample-case`, based on public main
`bc7dd603e2d9d6da185cedfe9f3ce3dd05fa9d79`. This is a separate clone. No push,
deployment, model invocation, original-image access or cloud configuration
change was performed. This is local implementation evidence, not a hosted
launch or challenge-eligibility claim.

## Decision and usable scope

Ship **`/try/` — Sample Case Mode** as the external visitor entry. The
existing static public surfaces do not provide a verified private upload,
job-isolation or deletion service. Accepting outside files is deferred.

Visitors can select 1–6 already-public brand-approved derivatives, choose
product/detail coverage, a people constraint and a pixel minimum, and inspect
the actual existing gates' result for that combination. They can keep
Shortlist candidates or defer, add a note, download the decision with evidence
and unresolved questions, and clear the active page. Changing the brief or
image set invalidates prior choices. Missing brief means no shortlist.

This is **interactive recorded evidence**, not a live agent or a fresh Astra
image review. Recorded observations came from the existing Gemini run.
Astra implemented this external experience. No free-text brief parser is
implied. Instagram and the supplied NUDE-01 product fact remain fixed.

## Exact code map

| File | Responsibility |
| --- | --- |
| `tools/build_sample_case.py` | Calls existing verified `run()`, `gate()` and `compute_coverage()`; compiles 19 brief states × 63 nonempty subsets = 1,197 cases; rejects source/image mismatches and consulted stub facts. |
| `ui/sample/cases.json`, `integrity.js` | Reproducible public allowlisted results and SHA-256 pin. No raw responses, private paths, resolvers or credentials. |
| `ui/sample/index.html`, `sample.css` | New bounded visitor flow, based on the existing runtime stylesheet; evidence and privacy explanations. |
| `ui/sample/core.mjs` | Validated case lookup and human decision export; no new publishing-gate implementation. |
| `ui/sample/app.js` | SHA and decode checks, accessible controls, display, tab-memory state and local JSON download. |
| `tools/build_pages.py` | Adds `/try/` and explicit cross-link rewrites to the existing Pages build. |
| `ui/workroom/brief-established.html`, `brief-missing.html`, `ui/runtime/index.html` | One “Try a sample case” navigation link each. |
| `.github/workflows/pages.yml` | Watches `ui/sample/**` for the existing main-branch Pages workflow. |
| `tests/test_sample_case.py`, `tests/sample_core.test.mjs` | Gate parity, provenance, coverage, selection/export, public payload and packaging checks. |

The evidence route, publishing gate, vocabularies, sealed inputs, signals,
brief-v1, recorded result JSON, original runtime CSS and public photo bytes
are unchanged. The 400-photo presentation remains an explicitly separate
study. All six sample observations remain NEW; no UNKNOWN/CONFLICT examples
are invented. Unknown publishing facts remain visible as pending questions.

## Run and regenerate

From the repository root, a static preview needs only Python:

```bash
python3 tools/build_pages.py --out _site
python3 -m http.server 8782 --bind 127.0.0.1 --directory _site
```

Open `http://127.0.0.1:8782/try/`. Use HTTPS or localhost, not `file://`;
Web Crypto verifies the case and the six images before exposing candidates.
The build's `--out` is a disposable staging directory, never a source folder.

To reproduce the cases and run the verification suite:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt Pillow
.venv/bin/python tools/build_sample_case.py --check
.venv/bin/python -m unittest discover -s tests -q
node --test tests/sample_core.test.mjs
```

No API key, cloud identity or model invocation is needed for these commands.
If an authorized evidence or gate revision occurs, regenerate with
`.venv/bin/python tools/build_sample_case.py`, inspect the JSON delta and
rerun the same checks. Do not edit `cases.json` by hand or unpin sealed data.

Source lineage currently included in the case:

- Recorded receipt SHA-256: `15536244669f8e2b6b76f8df5a3e03dc2f2cf4f45e870716c5a759e5b3fca709`
- Tracked replay SHA-256: `6505e8b1f55f12aa569c4d48f2f735ea4acb796587902f580f6ea2e8767e53e3`
- Case payload SHA-256: `9d3bca48357427583f0c4b0307e32bdf8b624cc28b5cd13197dfdaeafe3a18f0`

## Verification performed

- Python: 135 tests ran, OK, one expected skip because the original private
  receipt is absent from this clean clone. All 1,197 supported cases match
  the existing Python gate and coverage function.
- Node: 6 tests passed, including every supported case, invalid bindings,
  unresolvable choices, deferred decisions and evidence-preserving export.
- Pages: 31 files staged; all local links resolve. Existing routes remain.
- Actual Codex in-app browser: default full set gives 1 Shortlist / 2 Needs
  Review / 3 Remaining; detail-only gives 0 / 2 / 4; removing ROBE-5059 gives
  0 / 2 / 3 from five photos; missing brief gives 0 / 6 / 0 with no selection.
- A real download was read back from disk: 8,140-byte JSON, kept ROBE-5059,
  the synthetic test note and still-MISSING detail coverage; no image bytes.
  Browser event waiting timed out, but the actual downloaded file was
  independently present and parsed. Its SHA-256 was
  `3f1ddda368af3fe38a03894b71da4c0c290324c91320df9b1fe838426896a357`.
- Clear returned to the initial form, removed the note, reset all six photos
  and hid the previous result. Mobile setup and results with evidence open
  had `scrollWidth = clientWidth = 390`; actual rendering was inspected.
- Keyboard Enter applied the brief and Space kept the candidate. Reload
  cleared a synthetic note and selection. Desktop width and scroll width
  both measured 1,280 pixels; no browser console warnings or errors appeared.
- Corrupting a **staged copy only** of IG-262 stopped all candidates and named
  the image checksum failure. Altering staged case JSON stopped on its checksum.
  Restoring both files and retrying recovered the source wall. Tracked inputs
  were never modified by these checks.

Browser results are a focused local smoke check, not an accessibility
certification or an all-browser guarantee. Hosted responses and deployment
headers have not been checked for this new route.

## Privacy and operational boundaries

There is no file input, drag/drop upload, API credential field or upload
endpoint. Only existing public assets and compiled results are fetched from
the same static host. No application analytics, cookie storage, localStorage,
sessionStorage, URL serialization or server writes are added. A restrictive
page CSP disallows external scripts, connections and form submissions; this
does not claim host-level security certification.

Visitor brief, choices and note live in page memory. Clear/reload starts over;
page restoration resets controls. The browser and host can retain public
assets or normal access logs under their own policies. A downloaded decision
is a separate user-controlled file; Clear does not delete it. No secure-erasure
claim is made. No private user material is included in the public build.

Before a future real-upload version, separately implement and verify private
storage outside the public build/repo, per-job isolation, bounded image and
request sizes, server-side credentials, provider/data-flow disclosure, abuse
and cost limits, explicit retention, and deletion behavior including failed
jobs. Nothing in this patch authorizes or implements that path.

## Apply and publish handoff

The local deliverable is a Git format-patch against the base above. In a clean
review checkout at that base:

```bash
git switch -c launch/sample-case-review bc7dd603e2d9d6da185cedfe9f3ce3dd05fa9d79
git am /absolute/path/to/second-eyes-sample-case.patch
```

Run the commands above and review `/try/`. If main has advanced, apply in an
isolated checkout and resolve only the narrow integration delta; do not reset
the owner's checkout. The preserved landing page still opens the historical
Workroom; use `/try/` as the proposed Product Hunt visit URL.

After Crystal accepts this concrete result, the release owner can merge it
through the existing Pages workflow. Then verify the live `/try/`, `/runtime/`
and Workroom at desktop and mobile sizes; exercise Keep, JSON download,
Clear, missing brief and the stricter brief. The workflow currently stages
and checks links; it does not replace the Python/Node review tests above.
No live endpoint or fresh Astra review should be claimed in launch copy.

## Sources actually consulted, in requested order

1. [GitHub current product](https://github.com/Crystal32378/second-eyes-agent)
   at the base commit above; contracts, runtime and data boundaries read.
2. [Existing Workroom](https://crystal32378.github.io/second-eyes-agent/brief-established.html)
   and its linked recorded runtime; actual rendered product inspected.
3. [Devpost](https://devpost.com/software/second-eyes): historical submission,
   not evidence that an external upload service exists.
4. [AWS Builder deployment/runtime account](https://builder.aws.com/content/3J6GueLsCCEOMZeSxfUJm9vPx3E/second-eyes-for-agents-for-humans-an-professional-fashion-editorial-agent-built-for-the-brand-team-that-knows-how-to-save-time-and-when-not-to-guess),
   linked from Devpost; distinguishes the public presentation from runtime evidence.
5. [Product Hunt Astra Challenge](https://www.producthunt.com/contests/gpt-6-astra-challenge):
   new external-entry constraint. The page showed September 18, 2026; detailed
   eligibility and deadline timezone were not verified, so no acceptance claim.
6. [YouTube demo](https://www.youtube.com/watch?v=uSYH90j3dls): description,
   transcript and an opening frame inspected; not a full video playback review.
