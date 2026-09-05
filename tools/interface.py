"""Four tool interfaces — signatures + logging only, no inference in Phase 1.

1. inspect_asset   — read image/video bytes, return observable handle
2. get_existing_info — read manifest row + canonical pointers (Batch A) /
                       fixture-provided old label (synthetic)
3. record_result    — append fresh output record to outputs/
4. ask_human       — enqueue CONFLICT/UNKNOWN with attached evidence
"""

from typing import Any, Dict


def inspect_asset(asset_key: str, kind: str) -> Dict[str, Any]:
    raise NotImplementedError("Phase 1 interface only; wired in Phase 2 runner")


def get_existing_info(asset_key: str) -> Dict[str, Any]:
    raise NotImplementedError("Phase 1 interface only; wired in Phase 2 runner")


def record_result(record: Dict[str, Any]) -> None:
    raise NotImplementedError("Phase 1 interface only; wired in Phase 2 runner")


def ask_human(evidence: Dict[str, Any]) -> str:
    raise NotImplementedError("Phase 1 interface only; wired in Phase 2 runner")
