"""Strands agent loop skeleton — NO model calls in Phase 1.

Locked loop (5 steps):
  receive task -> inspect asset -> retrieve existing info -> compare -> decide

Decisions are STRUCTURAL, not prompt-based: tools return evidence or empty,
and a pure rule function routes CLEAR / CONFLICT / UNKNOWN. The model only
describes what it sees and never decides sufficiency — there is no interface
for it to assert what it was not given:

  evidence present + consistent -> CLEAR
  evidence present + conflicting -> CONFLICT (to human)
  evidence insufficient         -> UNKNOWN (never call the model to fill in)

Model invocation is quarantined behind run_synthetic.py / run_batchA.py,
both of which are BLOCKED until the Bedrock daily token quota recovers.
"""

from dataclasses import dataclass
from typing import Literal

from runtime.vocab import FIELDS, normalize

Decision = Literal["CLEAR", "CONFLICT", "UNKNOWN"]

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


def route(evidence: dict) -> Decision:
    """Pure rule function — no model call. The ONLY decider of sufficiency.

    Closed-vocab comparison (deterministic program, never model judgment):

      observed: {"colour": token|None, "item": token|None, "shot": token|None}
      old:      same shape (parsed old label; prose/"很有故事感" -> all None)

    Rules (exactly THREE states; degenerate inputs fold into UNKNOWN):
      - observed has nothing in-vocab            -> UNKNOWN
      - old has nothing in-vocab                 -> UNKNOWN (nothing to verify)
      - same field, both in-vocab, unequal       -> CONFLICT
      - >=1 comparable field, all equal          -> CLEAR

    Examples:
      old colour=red vs observed colour=beige    -> CONFLICT
      old "很有故事感" vs observed colour=beige  -> UNKNOWN (non-comparable)
    """
    observed = evidence.get("observed") or {}
    old = evidence.get("old") or {}
    obs = {f: normalize(f, observed.get(f)) for f in FIELDS}
    prev = {f: normalize(f, old.get(f)) for f in FIELDS}
    if not any(obs.values()):
        return "UNKNOWN"
    if not any(prev.values()):
        return "UNKNOWN"
    for f in FIELDS:
        if obs[f] is not None and prev[f] is not None and obs[f] != prev[f]:
            return "CONFLICT"
    return "CLEAR"
