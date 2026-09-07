# Second Eyes — second-eyes-agent (local working folder, not yet public)

Professional track — Agents for Humans Hackathon.

> Second Eyes — 它先看一遍。沒證據不猜，有衝突才問你。

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
  empty; a pure rule function decides CLEAR / CONFLICT / UNKNOWN on closed
  vocabularies. The model only describes what it sees and NEVER decides
  routing — its selections require a verifiable evidence_ref (frame
  timestamp, crop, or tool-result ID) or they are discarded, and every one
  is logged with its ref for human audit.
- Model runs BLOCKED on Bedrock daily token quota (ThrottlingException).
  No mock results are presented as Bedrock results.
- Protocol: synthetic 3–5 cases first → lock prompt/tools → Batch A 60 blind run.
  Batch A only. Personnel out of scope.
