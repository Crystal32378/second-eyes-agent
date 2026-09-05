"""Run logging / provenance — every run appends tool calls + decision + timestamps.

No model calls here. Runners import this module.
Each output record must carry: asset_key, kind, tool_calls[],
decision (CLEAR/CONFLICT/UNKNOWN), model id (when run), timestamps.
"""
import datetime
import json
import os

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def append_record(record: dict, filename: str = "run_log.jsonl") -> None:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    path = os.path.join(OUTPUTS_DIR, filename)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
