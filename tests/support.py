"""Shared test fixtures — the suite must run on a clean clone.

outputs/ is git-ignored, so a fresh clone has no outputs directory and no
local MVP file. Tests that need one build it here from the TRACKED replay
input rather than assuming this machine already has it.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
LOCAL_MVP = OUTPUTS / "local-mvp.json"


def ensure_outputs() -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    return OUTPUTS


def ensure_local_mvp() -> Path:
    """Build outputs/local-mvp.json from the tracked replay input."""
    from runtime.local_mvp import run
    ensure_outputs()
    if LOCAL_MVP.is_file():
        return LOCAL_MVP
    results, error = run()
    if error:
        raise AssertionError("local MVP recompute failed: {}".format(error))
    LOCAL_MVP.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    return LOCAL_MVP
