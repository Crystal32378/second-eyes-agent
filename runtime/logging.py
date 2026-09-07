"""Run logging / provenance — every run appends tool calls + decision + timestamps.

No model calls here. Runners import this module.

Record schema (all fields required):
  asset_key, kind, tool_calls[], decision (CLEAR/CONFLICT/UNKNOWN/NEW),
  model (id, when run), timestamps, evidence: {"observed": {field:
  {"value": token, "ref": frame timestamp / crop / tool-result ID}}}.

The evidence+ref block is what "logged with its ref for human audit"
means: any observed selection WITHOUT a ref is rejected by
validate_record() before it can be written. CONFLICT/UNKNOWN records
additionally carry "human_queue": true (NEW/CLEAR carry false).
"""
import datetime
import json
import os

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")

REQUIRED_FIELDS = ("asset_key", "kind", "tool_calls", "decision",
                   "model", "timestamps", "evidence")

HUMAN_QUEUE = {"CONFLICT": True, "UNKNOWN": True,
               "CLEAR": False, "NEW": False}


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def validate_record(record: dict) -> dict:
    """Enforce the schema. Raises ValueError on violation.

    In particular: every observed selection must carry a non-empty ref;
    ref-less selections are rejected, never written.
    """
    for field in REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"record missing field: {field}")
    if record["decision"] not in HUMAN_QUEUE:
        raise ValueError(f"unknown decision: {record['decision']}")
    observed = (record["evidence"] or {}).get("observed") or {}
    for fname, sel in observed.items():
        if sel is None:
            continue
        if not isinstance(sel, dict) or not sel.get("value") or not sel.get("ref"):
            raise ValueError(f"observed {fname} lacks value or ref: {sel!r}")
    record.setdefault("human_queue", HUMAN_QUEUE[record["decision"]])
    return record


def append_record(record: dict, filename: str = "run_log.jsonl") -> None:
    validate_record(record)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    path = os.path.join(OUTPUTS_DIR, filename)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
