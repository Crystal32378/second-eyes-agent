# Second Eyes — second-eyes-agent

Professional track — Agents for Humans Hackathon (Strands Agents SDK).

> Second Eyes hands you a shortlist first.
> Most things stay filed. Questions come to you.

**Product (one line):** for a 400-photo publishing deadline, Second Eyes
delivers a shortlist with a reason and pending items per photo — the human
picks the final three by instinct. No hero ranking, no taste, no guessing.

**Boundary (standing):** no brief = no clearance basis; every photo is
"needs review" at best. Second Eyes checks ONLY what the brief states and
endorses no contract, licence, or legal status. "Candidates matching the
brief's known conditions" — never "cleared".

**Architecture:** see [docs/architecture.md](docs/architecture.md) — it marks
exactly what is implemented vs presentation-only. Anything the diagram shows
dashed (brief parsing, live 400-run, clustering, coverage computation,
video adapter, Batch A blind run) is spec/mock, not runtime.

## Evidence distinction (400-photo demo)

- **404 real source files were scanned** (local IG / IG Reel corpus) and are
  presented as a **400-photo publishing scenario**: SHORTLIST 18, NEEDS
  REVIEW 7, REMAINING 375 (300 brief mismatch + 60 near-duplicates + 15
  technical). Counts and placements in the static UI are illustrative mock
  content with real reference images — not model outputs.
- The 12 in-repo demo derivatives (`ui/workroom/assets/`) are compressed,
  metadata-stripped crops made for this demo from brand-supplied situational
  photographs (social-media usage rights confirmed by the asset owner). Not
  product assets, not archive originals, not representative archive contents.
  No release or clearance assessment. No clearly identifiable full face.
- The separate 60-asset Batch A evaluation corpus (54 images + 6 videos,
  non-Personnel) is **private evaluation infrastructure**: membership is
  hash-gated, bytes stay read-only off-repo, and the blind run has NOT been
  executed. Nothing in this repo claims Batch A results.

## Implemented (this repo, tested)

- Strands agent loop + pure deterministic `route()` → CLEAR / CONFLICT /
  UNKNOWN / NEW (15/15 unit tests; routing is structural, never prompt-based)
- Strands + Gemini provider adapter (Vertex AI, image only; video is
  structurally unsupported on this path)
- Fresh-agent-per-fixture isolation; attached `evidence_ref` required
  (ref-less selections are discarded); validated JSON run records with
  token usage
- Frozen closed vocabularies (colour/item/shot, CJK substring scan)
- 6 SHA-pinned synthetic fixtures (prove plumbing only — never accuracy)
- Static Publishing Workroom UI (two states) + synthetic 4-state viewer

## Presentation-only (not wired)

Brief parsing, live shortlist run, near-duplicate clustering, coverage
computation, automatic zone population, final-three handoff, video adapter,
Reel Crew handoff. See `docs/shortlist-brief.md` (input spec, no runner).

## Install & test

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v   # 15/15 expected
```

## Open the static Workroom (no server needed for files, but images load
best over localhost)

```bash
cd second-eyes-agent && python3 -m http.server 8123
# http://localhost:8123/ui/workroom/brief-established.html
# http://localhost:8123/ui/workroom/brief-missing.html
# http://localhost:8123/ui/   (synthetic 4-state viewer)
```

## Run the synthetic path (Gemini via Vertex ADC; image fixtures only)

```bash
GOOGLE_CLOUD_PROJECT=<project> .venv/bin/python runtime/check_gemini.py --invoke
GOOGLE_CLOUD_PROJECT=<project> .venv/bin/python runtime/run_synthetic_gemini.py --only SYN-CLEAR-01
```

Video fixtures log `BLOCKED_UNSUPPORTED` (Strands GeminiModel has no video
blocks). Never present Gemini results as Nova evidence. Nova remains
quota-blocked; see `docs/quota_status.md`.

## Pre-existing work — DISCLOSED (not claimed as new)

The following existed before the hackathon Submission Period and are used
ONLY as read-only evaluation corpus / reference:

- Batch A selection: 60 assets (54 images + 6 videos), non-Personnel only
  (`sample_order` 1–60 of the observation sample manifest). Bytes and
  manifest live off-repo; configure via `SECOND_EYES_MANIFEST` and
  `SECOND_EYES_SOURCE_ROOT` (never committed).
- Existing semantic observations, technical inventory, Stage 3 canonical
  identity registry/crosswalk, and any Brand Library schema / taxonomy /
  resolver / UI / code / policy / logs (evaluator-only reference).
- Hero image desk items are desaturated, aged crops derived from situational
  photographs gifted by the brand's photographer with social-media usage
  rights. Not product assets, not archive originals, and not presented as
  representative archive contents.

## Hackathon-new (only these are claimed)

This repo's agent loop, tools, providers, runners, frozen vocabularies,
synthetic fixtures, logging, static UIs, docs, and submission materials.
No Brand Library code is copied into this project.

## Status

- Static public gate: `ui/workroom/` ships real compressed derivatives, zero
  symlinks, English UI, reconciled 400 counts.
- Model runs: synthetic plumbing proven on image fixtures; Batch A 60 blind
  run pending; no accuracy claimed anywhere.

## License

MIT — see [LICENSE](LICENSE).
