# Second Eyes — Deploy manifest (measured vs reported)

> Rule: this file separates **measured this session** from **historical reports**.
> No redeploy and no model calls were made while writing it.

## 1. Measured this session (2026-09-12T09:17:49Z, read-only, curl + sha256)

- Branch: `main @ 1c10071`, working tree clean, `origin/main` in sync.
- Local source: `ui/workroom/` (commit `a6217a1` ships Pages workflow).
- Live URLs probed with plain GET (no deploy, no model call):
  - Amplify: `https://main.dvx4tmt6s6hty.amplifyapp.com`
  - GitHub Pages: `https://crystal32378.github.io/second-eyes-agent`
  - App ID (from Amplify hostname, user-supplied): `dvx4tmt6s6hty`

### 1.1 Dual-host hash comparison — zero differences

| File | Local sha256 | Amplify | Pages | Result |
|---|---|---|---|---|
| `index.html` (`/` redirect) | `55c75a61…5d1245` | `55c75a61…5d1245` | `55c75a61…5d1245` | MATCH |
| `brief-established.html` | `0642a1ce…c9952` | `0642a1ce…c9952` | `0642a1ce…c9952` | MATCH |
| `brief-missing.html` | `5c58c466…88826` | `5c58c466…88826` | `5c58c466…88826` | MATCH |
| `styles.css` | `3b3a3188…677e4` | `3b3a3188…677e4` | `3b3a3188…677e4` | MATCH |
| `assets/BACK-5F20.jpg` | `0f0b8a25…7992bc` | match | match | MATCH |
| `assets/IG-072.jpg` | `d6194c72…0b5fa5f` | match | match | MATCH |
| `assets/IG-245.jpg` | `cceb560e…2e8f4f` | match | match | MATCH |
| `assets/IG-256.jpg` | `fd47143c…d005f5` | match | match | MATCH |
| `assets/IG-262.jpg` | `074fda08…76f2c5a` | match | match | MATCH |
| `assets/IG-277.jpg` | `2210d695…452f004` | match | match | MATCH |
| `assets/IMG-4489.jpg` | `cf59ada9…bffffe6d` | match | match | MATCH |
| `assets/MV-BLK.jpg` | `9ab192f0…f79a419b` | match | match | MATCH |
| `assets/REEL-045.jpg` | `cc33f80f…2e773dcd` | match | match | MATCH |
| `assets/REEL-050.jpg` | `ebd30185…792fedf3` | match | match | MATCH |
| `assets/ROBE-5059.jpg` | `d3aeced9…122e95e1` | match | match | MATCH |
| `assets/WEAR-8106.jpg` | `5e6bebf0…31a1d91` | match | match | MATCH |

Method: `curl -sSL <host>/<path> | sha256sum` compared against
`sha256sum ui/workroom/...`. Images were hashed as bytes only;
no image pixels were loaded into the agent context.

Differences found: **none**. Both hosts serve byte-identical
workroom (presentation-only static frontend, runtime not wired).

## 2. Historical reports (not re-verified this session)

- Previous棒 reported: AWS Amplify static deployment via **AWS API
  manual ZIP deploy**, URL `https://main.dvx4tmt6s6hty.amplifyapp.com`,
  GitHub Pages retained, frontend presentation-only, runtime not connected.
- Weekend Challenge article reported as published at
  `https://builder.aws.com/content/3JDk3T82TtEIxFG9lsC6wTN5fc7/weekend-deployment-challenge-second-eyes`
  (not fetched this session).
- No `amplify.yml`, `amplify/` config, or `DEPLOY.md` exists in-repo;
  the ZIP-deploy claim lives only in session handoff, not in git history.
  `git log` shows only the Pages deploy commit (`a6217a1`).

## 3. Video line (v3.1 is current; v1 handoff is superseded)

Verified on disk 2026-09-12 (stat + sha256 + srt line count, no playback):

- Current: `video-handoff/second-eyes-demo-v3.1.mp4`
  `43628531 bytes`, mtime `Sep 12 10:21:10 2026`,
  sha256 `7a48ced306c463fad5ecd196649c6f976ed7fc7d5106d4e2e1a83962d88d84e5`.
- Subtitles: `second-eyes-demo-v3.1.srt`, 123 lines / 31 cues,
  ends with "This is Crystal, signing off."
  (`build/subtitles/second-eyes-demo-v3.1.srt` identical line count).
- `video-handoff/HANDOFF-TO-KIMI.md` describes **v1 picture-lock +
  narration rescue only** (210s, gaps 60–150s). Do NOT cite it as current
  status; v3/v3.1 (`build/base-v3.mp4`, `build/v3-plan.json`,
  `build/v3narr/`) supersede it.

## 4. Status carried forward

- Static public gate ships real compressed derivatives, zero symlinks,
  English UI, reconciled 400 counts — mock placements, not model outputs.
- Runtime remains presentation-only on both hosts (see
  `docs/architecture.md` dashed nodes). Next step is the minimal wiring
  proposal below; no model call, no redeploy in this session.

## 5. Minimal runtime wiring proposal (no code changed this session)

Goal: `fixed brief → approved small image set → real observation +
rule routing → UI reads results`. No accuracy claims, no clearance claims.

Existing (reuse as-is):
- `agent/loop.py::route()` — pure CLEAR/CONFLICT/UNKNOWN/NEW, 15/15 tests.
- `runtime/vocab.py` — FROZEN colour/item/shot, CJK substring scan.
- `agent/providers.py` — Gemini via Vertex, image-only, temp 0.
- `runtime/run_synthetic_gemini.py` — fresh Agent per fixture, SHA check,
  mechanical ref attach, validated JSON + raw log to `outputs/`.
- `runtime/logging.py::validate_record` — ref-less selections rejected.
- `fixtures/synthetic/cases.json` — 6 SHA-pinned cases with `ref`.
- `docs/shortlist-brief.md` — input spec (no runner yet).

Missing contracts (must add before any live run):

> Contract status (explicit): the existing `route()` is per-photo
> evidence routing only. It is NOT shortlist logic. Shortlist / Needs
> Review / Remaining are publishing buckets that require a brief gate +
> coverage pass which do not exist yet. Nothing below is implemented.

1. `brief.json` schema (fixed): required scenes, hard constraints,
   supplied facts. Rejects inference; everything absent → 待確認.
2. `small-set manifest`: 6–12 approved derivatives only
   (from the 12 in `ui/workroom/assets/`), each with `asset_key`,
   `sha256`, `old_label` (or explicit `none`), `ref` convention
   (e.g. `workroom:frame-full`). No full corpus, no new pixels.
3. `observation runner` (image-only): locked prompt + frozen vocab,
   model describes only, runner attaches ref mechanically,
   `route()` decides, `validate_record` gates `outputs/`. Video =
   `BLOCKED_UNSUPPORTED`, never frame-extracted silently.
4. `ui/results.json` reader: static UI renders `outputs/*.jsonl`
   decisions + refs + pending items; mock SHORTLIST 18 / NEEDS REVIEW 7
   counts stay labelled illustrative until replaced by real run output.

### 5.1 Evidence states → brief verdict → buckets (PROPOSED contract, not implemented)

`route()` outputs a per-photo evidence state only (observed-vs-old on
frozen vocab). It decides NO bucket. Bucket assignment belongs to the
not-yet-built **brief-gate**, whose verdict per photo is one of three:
**符合 / 明確不符 / 證據不足** (against `brief.json`: required scenes,
hard constraints, channel fit, supplied facts). Coverage (HAVE / MISSING
per scene; MISSING stays missing) is computed after.

- `CLEAR` must still pass the brief-gate. CLEAR + 符合 → Shortlist
  candidate; CLEAR + 明確不符 → Remaining with reason.
- `NEW` must also enter the brief-gate; it does NOT default to
  Remaining. NEW + 符合 → Shortlist candidate; NEW + 明確不符 →
  Remaining; NEW + 證據不足 → Needs Review.
- Blocking conflicts go to Needs Review: `CONFLICT` / `UNKNOWN`, or any
  state where the brief-gate verdict is 證據不足 (cannot tell scene /
  constraint satisfaction). Each card names what is blocking, who can
  resolve it, and what is needed. Never auto-filed, never ranked.

Cases (illustrative, rules only):
- CLEAR + 符合 → Shortlist: observed beige product matches old label
  AND satisfies requested detail scene, constraints pass, SKU live.
- CLEAR + 明確不符 → Remaining: observed matches old label BUT fails
  brief (e.g. wrong scene slot, channel format fails, SKU not live).
- NEW + 符合 → Shortlist: no old label, but observed satisfies a
  requested scene with constraints passing (e.g. clean hanging robe
  fills detail slot). Not default-Remaining.
- NEW + 證據不足 → Needs Review: observable token exists but scene fit
  cannot be determined (e.g. crop shows fabric only, cannot tell
  hero vs detail).
- CONFLICT → Needs Review: old claims red vs observed beige on the
  same field; human resolves which record is wrong.
- UNKNOWN → Needs Review: no valid in-vocab observation with ref;
  nothing to check against brief, human decides.

Who checks brief conditions: the **brief-gate** (missing component),
not `route()`. `route()` checks structural comparability
(common vocab field equal or not); the brief-gate checks required
scenes, hard constraints, channel fit, and supplied facts, then computes
coverage (HAVE / MISSING per scene; MISSING stays missing, never guessed).
Until the brief-gate exists, any Shortlist/Needs Review/Remaining counts
on screen remain mock placements.

Acceptance (no model call needed to define):
- `unittest discover -s tests` still 15/15.
- One dry run with `--only SYN-CLEAR-01`-style plumbing on the small set
  produces validated JSONL where every observed selection has a `ref`,
  `human_queue` flags match CONFLICT/UNKNOWN=true, and UI shows
  reason + ref + pending per card with no ranking/score.
- Brief-missing gate: with `brief.json` absent, UI shows the
  `brief-missing.html` state and no shortlist is generated.
