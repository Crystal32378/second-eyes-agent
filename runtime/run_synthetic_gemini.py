#!/usr/bin/env python3
"""Gemini synthetic run — Strands -> Vertex gemini-2.5-flash over fixtures.

Protocol:
  1. Prompt is LOCKED (runtime/synthetic_prompt.py, committed pre-run).
  2. Vocab is FROZEN. No post-result tuning — on any prompt/tool/fixture
     problem: STOP, log, report. Do not adjust and re-run silently.
  3. Per fixture: verify media SHA, send media + locked prompt, parse strict
     JSON selections, attach fixture-declared refs MECHANICALLY (the runner,
     not the model, supplies refs), route() decides, validate + save record.
  4. Raw model responses are saved verbatim alongside routing records.
  5. Batch A is NEVER touched here. Gemini results are NEVER Nova evidence.

Usage:
  GOOGLE_CLOUD_PROJECT=<proj> .venv/bin/python runtime/run_synthetic_gemini.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR in sys.path:
    sys.path.remove(SCRIPT_DIR)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from strands import Agent  # noqa: E402

from agent.loop import route  # noqa: E402
from agent.providers import DEFAULT_GEMINI_MODEL, build_gemini_model  # noqa: E402
from runtime.logging import append_record, utcnow  # noqa: E402
from runtime.synthetic_prompt import OBSERVE_PROMPT, PROMPT_VERSION  # noqa: E402
from runtime.vocab import FIELDS, normalize  # noqa: E402

FIXTURES = ROOT / "fixtures" / "synthetic" / "cases.json"
MEDIA_DIR = ROOT / "fixtures" / "synthetic"


def parse_selection(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else ""
    try:
        data = json.loads(text.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"PROMPT_ISSUE: non-JSON model output: {raw!r}") from e
    if not isinstance(data, dict) or set(data) != set(FIELDS):
        raise RuntimeError(f"PROMPT_ISSUE: wrong JSON shape: {raw!r}")
    out = {}
    for f in FIELDS:
        v = data[f]
        if v == "NONE":
            out[f] = None
        elif normalize(f, v) is None:
            raise RuntimeError(
                f"PROMPT_ISSUE: out-of-vocab selection {f}={v!r}")
        else:
            out[f] = normalize(f, v)
    return out


def main() -> int:
    model_id = os.getenv("SECOND_EYES_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_name = f"synthetic_gemini_{stamp}.jsonl"
    raw_name = f"synthetic_gemini_{stamp}.raw.jsonl"

    cases = json.loads(FIXTURES.read_text())["cases"]
    agent = Agent(model=build_gemini_model(), system_prompt=OBSERVE_PROMPT,
                  tools=[], callback_handler=None)

    results = []
    for case in cases:
        media_path = MEDIA_DIR / case["media"]
        digest = hashlib.sha256(media_path.read_bytes()).hexdigest()
        if digest.lower() != case["sha256"].lower():
            raise RuntimeError(f"FIXTURE_ISSUE: sha mismatch {case['fixture_id']}")
        media_bytes = media_path.read_bytes()
        if case["kind"] == "image":
            fmt = media_path.suffix.lstrip(".").lower()
            block = {"image": {"format": fmt, "source": {"bytes": media_bytes}}}
        else:
            block = {"video": {"format": "mp4", "source": {"bytes": media_bytes}}}
        result = agent([block, {"text": "Observe and reply with strict JSON."}])
        raw = str(result).strip()
        selections = parse_selection(raw)  # raises PROMPT_ISSUE -> STOP
        ref = case["ref"]
        observed = {f: ({"value": selections[f], "ref": ref}
                        if selections[f] is not None else None)
                    for f in FIELDS}
        old = {"colour": case.get("old_label"), "item": case.get("old_label"),
               "shot": case.get("old_label")}
        decision = route({"observed": observed, "old": old})
        record = {
            "asset_key": case["fixture_id"],
            "kind": case["kind"],
            "tool_calls": ["inspect_media", "observe_gemini", "route"],
            "decision": decision,
            "model": model_id,
            "prompt_version": PROMPT_VERSION,
            "timestamps": {"started": utcnow(), "finished": utcnow()},
            "evidence": {"observed": observed,
                         "old_label": case.get("old_label"),
                         "selections": selections},
            "expects_routing": case["expects_routing"],
            "match": decision == case["expects_routing"],
        }
        append_record(record, filename=out_name)
        with open(ROOT / "outputs" / raw_name, "a") as f:
            f.write(json.dumps({"fixture": case["fixture_id"], "model": model_id,
                                "prompt_version": PROMPT_VERSION, "raw": raw}) + "\n")
        results.append((case["fixture_id"], decision, case["expects_routing"],
                        decision == case["expects_routing"]))
        print(f"{case['fixture_id']}: routed={decision} "
              f"expected={case['expects_routing']} "
              f"{'MATCH' if decision == case['expects_routing'] else 'DIFF'}")

    matched = sum(1 for r in results if r[3])
    print(f"SUMMARY: {matched}/{len(results)} routing matches "
          f"(informational only — fixtures prove plumbing, not accuracy)")
    print(f"records: outputs/{out_name}  raw: outputs/{raw_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
