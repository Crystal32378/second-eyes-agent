"""Strands agent loop skeleton — NO model calls in Phase 1.

Locked loop (5 steps):
  receive task -> inspect asset -> retrieve existing info -> compare -> decide

Decisions: CLEAR (act) / CONFLICT (ask human) / UNKNOWN (preserve).
Model invocation is quarantined behind run_synthetic.py / run_batchA.py,
both of which are BLOCKED until the Bedrock daily token quota recovers.
"""

from dataclasses import dataclass
from typing import Literal

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
