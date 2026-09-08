# Second Eyes — second-eyes-agent (local working folder, not yet public)

Professional track — Agents for Humans Hackathon.

> Second Eyes — 它先看一遍。沒證據不猜，有衝突才問你。
> Most things stay filed. Questions come to you.

Product framing (copy layer only — no system change): Second Eyes is a
**customs-clearance tool, not an organizing tool**. It tells you which
photos are cleared, which are blocked, and whose hands hold the keys —
and on the cell that could get you sued, it never guesses. Currently
demonstrated with synthetic fixtures; rights sources are not yet connected.

State relabel (same four states, no code change):
  CLEAR     兩邊說法一致      → 可用 (no detected conflict — candidate, not legal clearance)
  NEW       沒人說過話        → 你自己判 (no prior claim to dispute)
  CONFLICT  兩份說法打架      → 先別發
  UNKNOWN   缺清關依據        → 誰能解、要多久，寫在這裡

User-facing baskets (presentation only — evidence states stay internal):
  Ready candidate （未觸發已知風險，優先排）      ← CLEAR
  Needs review    （可能可用，缺一項確認）        ← NEW（缺首次確認）, UNKNOWN（缺依據+誰能解）
  Hold            （已有明確問題，不應直接發布）  ← CONFLICT

Honest scope: the four risk-tree steps (人物→清楚產品→畫面可用→發布條件)
are NOT all implemented — see docs/publish-risk-tree.md for what is wired
vs v-next. "Closest to publishable with no known risk triggered" is the
claim; "no-risk" never is.

## Pre-existing work — DISCLOSED (not claimed as new)

The following existed before the hackathon Submission Period and are used
ONLY as a read-only evaluation corpus / reference. None of their code,
schemas, observations, or outputs are claimed as hackathon-new:

- Batch A selection: 60 assets (54 images + 6 videos), non-Personnel only,
  membership authority `Minimax Lab/NUDE Agent Brand Library/00_observation/sample_manifest.csv`
  (`sample_order` 1–60), SHA-256 `653e987c…0f96e8563`.
- Source bytes: `Desktop/Brand Image/<rel_path>` (read-only, hash-gated per row).
- Selection/seed/method provenance: `sample_manifest_seed_and_method.md`.
- Existing semantic observations: `00_observation/observations.jsonl`
  (evaluator-only, NEVER fed to runtime before blind run).
- Technical inventory: `01_inventory/inventory.csv` + summaries / rebuild docs
  (evaluator-only reference).
- Stage 3 canonical identity registry + crosswalk (`registry_v1/`,
  `source_instances_v1.jsonl` + `source_asset_crosswalk_v1.jsonl`)
  — canonical pointers only (`canonical_asset_id`, `source_instance_id`,
  `source_relative_path`, `sha256`, `byte_size`, `source_root_id`).
  Legacy `NUDE-xxxxx` sample IDs are NOT canonical IDs.
- Any Brand Library schema / taxonomy / resolver / UI / code / policy / logs.
- Hero image desk items are desaturated, aged crops derived from situational
  photographs gifted by the brand's photographer with social-media usage
  rights. Not product assets, not archive originals, and not presented as
  representative archive contents.

## Hackathon-new (only these are claimed)

- This repo skeleton, Strands agent loop, 4 tools, Batch A hash-gated reader,
  decision/review flow, local UI outputs, run logs, fresh outputs,
  architecture, demo + submission materials.
- No Brand Library code is copied into this project.

## Status

- Phase 1 (no model quota needed): skeleton + disclosure + synthetic
  multimodal fixtures (3 images + 2 videos, clearly-synthetic, SHA-pinned in
  `cases.json`) + tool interfaces + logging + reader hash gate. No Bedrock calls.
- Routing contract (structural, not prompt-based): tools return evidence or
  empty; a pure rule function decides CLEAR / CONFLICT / UNKNOWN / NEW on
  frozen closed vocabularies (see runtime/vocab.py freeze note). The model
  only describes what it sees and NEVER decides routing — its selections
  require an attached evidence_ref (frame timestamp, crop, or tool-result
  ID) or they are discarded, and every one is logged with its ref for
  human audit. No old label -> NEW (recorded unverified, quiet), never
  an excuse to bother a human over an unlabelled file.
- Nova model runs remain BLOCKED on Bedrock daily token quota
  (ThrottlingException). No mock or Gemini result is presented as Nova
  evidence. A separate Strands + Gemini provider adapter is available for a
  quota-independent connectivity path; see `docs/gemini_status.md`.
- Protocol: synthetic 3–5 cases first → lock prompt/tools → Batch A 60 blind run.
  Batch A only. Personnel out of scope.
