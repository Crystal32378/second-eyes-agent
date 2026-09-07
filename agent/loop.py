"""Strands agent loop skeleton — NO model calls in Phase 1.

Locked loop (5 steps):
  receive task -> inspect asset -> retrieve existing info -> compare -> decide

Decisions are STRUCTURAL, not prompt-based: tools return evidence or empty,
and a pure rule function routes CLEAR / CONFLICT / UNKNOWN / NEW on frozen
closed vocabularies. The model only describes what it sees and never decides
routing — its selections require an attached evidence_ref or are discarded,
and every one is logged with its ref for human audit:

  nothing valid observed               -> UNKNOWN (ask human)
  observed, no old label               -> NEW (record + ref, unverified, quiet)
  observed + old, no common field      -> UNKNOWN (ask human)
  common field unequal                 -> CONFLICT (ask human)
  all common fields equal              -> CLEAR

Model invocation is quarantined behind run_synthetic.py / run_batchA.py,
both of which are BLOCKED until the Bedrock daily token quota recovers.
"""

from dataclasses import dataclass
from typing import Literal

from runtime.vocab import FIELDS, normalize, scan_old

Decision = Literal["CLEAR", "CONFLICT", "UNKNOWN", "NEW"]

MODEL_BLOCKED_REASON = (
    "Bedrock daily token quota ThrottlingException; "
    "no model calls until quota recovers. No mocks as Bedrock results."
)


@dataclass
class AgentTask:
    asset_key: str  # rel_path for Batch A; fixture id for synthetic
    kind: str       # image | video
    source_ref: str


def decide_placeholder() -> str:
    """Phase 1 stub. Real decide() lives in the Strands agent and runs
    only via the gated runners after quota recovery."""
    raise RuntimeError(f"Model-gated: {MODEL_BLOCKED_REASON}")


def _observed(field: str, raw) -> str | None:
    """Observed selections MUST carry an attached evidence_ref
    (frame timestamp, crop, or tool-result ID). A legal token WITHOUT
    a ref is discarded — closed vocab alone cannot prove the token came
    from image evidence, so ref-less selections never route anything."""
    if isinstance(raw, dict):
        value, ref = raw.get("value"), raw.get("ref")
    else:
        value, ref = raw, None
    tok = normalize(field, value)
    if tok is None or not ref:
        return None
    return tok


def route(evidence: dict) -> Decision:
    """Pure rule function — no model call. The ONLY decider of sufficiency.

    Closed-vocab comparison (deterministic program, never model judgment).
    The model only supplies observations WITH evidence_refs; every one is
    logged with its ref for human audit. The model NEVER decides routing.

      observed: {"colour": {"value": token, "ref": ref}|None, ...}
        (exact vocab token + frame timestamp / crop / tool-result ID)
      old:      free text per field, substring-scanned (CJK-safe);
                prose/"很有故事感" -> all None

    Order (exactly FOUR states; degenerate inputs fold into UNKNOWN):
      - no valid observation (in-vocab + ref)  -> UNKNOWN (ask human)
      - valid observation, no valid old value  -> NEW (record + ref,
        marked unverified, does NOT ask human; ~44/60 Batch A rows live here)
      - observation + old, no common field     -> UNKNOWN (ask human)
      - any common field unequal               -> CONFLICT (ask human)
      - all common fields equal                -> CLEAR

    NEW asserts nothing about the world — it records "model saw <token>
    here, ref attached". Observation != verified.

    Examples:
      old colour=red vs observed colour=beige  -> CONFLICT
      old "很有故事感" vs observed colour=beige -> NEW (old non-comparable)
      old colour=red vs observed item=dress    -> UNKNOWN (no common field)
    """
    observed = evidence.get("observed") or {}
    old = evidence.get("old") or {}
    obs = {f: _observed(f, observed.get(f)) for f in FIELDS}
    prev = {f: scan_old(f, old.get(f)) for f in FIELDS}
    if not any(obs.values()):
        return "UNKNOWN"
    if not any(prev.values()):
        return "NEW"
    common = [f for f in FIELDS if obs[f] is not None and prev[f] is not None]
    if not common:
        return "UNKNOWN"
    for f in common:
        if obs[f] != prev[f]:
            return "CONFLICT"
    return "CLEAR"
