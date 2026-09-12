#!/usr/bin/env python3
"""Model gate: manifest-driven real-image run, narrow scope.

Scope (locked for this gate):
- Only the 6 images in fixtures/smallset/manifest.json.
- One fresh Strands agent per photo, image blocks only. Any video
  kind or video extension refuses with exit 2 (zero video).
- Locked prompt (runtime/synthetic_prompt.py), frozen vocab
  (runtime/vocab.py), fixed brief (manifest's brief pointer).
  None of prompt/vocab/brief/fixture files are modified here.
- old labels are mechanically injected from the manifest (never from
  model output); refs are attached mechanically as the manifest's
  ref_convention (never supplied by the model).
- Non-model signals are NOT declared for this gate (scene/person/
  channel/SKU unknown): only long_edge is measured from bytes
  (source bytes:measured). The brief-gate therefore stops every photo
  at Needs Review on missing person signal — that IS the honest
  outcome being verified, alongside real observation plumbing.
- First anomaly stops the run immediately with a nonzero exit and a
  diag file. No retries, no silent reruns, no prompt/vocab edits.

Exit codes: 2 custody/brief/manifest, 3 schema (PROMPT_ISSUE),
4 provider/quota/transport.

Usage (from repo root; credentials via env, never committed):
  GOOGLE_CLOUD_PROJECT=<proj> .venv/bin/python \\
      runtime/run_smallset_gemini.py

Output (local only, git-ignored):
  outputs/smallset-gate_<stamp>.json  (items + summary + raw + usage)
  outputs/smallset-gate_<stamp>.diag.json (on stop: error + partial)
"""

from __future__ import annotations

import hashlib
import json
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
from agent.providers import (DEFAULT_GEMINI_MODEL,  # noqa: E402
                             build_gemini_model)
from runtime.brief_gate import gate  # noqa: E402
from runtime.smallset import verify_manifest  # noqa: E402
from runtime.synthetic_prompt import OBSERVE_PROMPT, PROMPT_VERSION  # noqa: E402
from runtime.run_synthetic_gemini import (parse_selection,  # noqa: E402
                                          usage_snapshot)

MANIFEST_PATH = ROOT / "fixtures/smallset/manifest.json"
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def fail(code: int, out_path: Path, error: str, detail: str,
         partial: list) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "complete": False, "error": error, "detail": detail[:500],
        "items_completed": len(partial), "partial": partial,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("STOP {}: {} (diag {})".format(error, detail[:200], out_path))
    return code


def main() -> int:
    import os
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = ROOT / "outputs" / "smallset-gate_{}.json".format(stamp)
    diag_path = ROOT / "outputs" / "smallset-gate_{}.diag.json".format(stamp)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    report = verify_manifest(manifest, ROOT)
    if not report["ok"]:
        return fail(2, diag_path, "CUSTODY",
                    "; ".join(report["errors"]), [])
    brief_path = ROOT / manifest["brief"]
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    entries = manifest["photos"]
    if len(entries) != 6:
        return fail(2, diag_path, "CUSTODY",
                    "manifest photo count != 6: {}".format(len(entries)), [])
    # Zero-video pre-scan: refuse before any model object is even built,
    # so no model call can precede the refusal.
    for entry in entries:
        if Path(entry["path"]).suffix.lower() in VIDEO_SUFFIXES:
            return fail(2, diag_path, "CUSTODY",
                        "{}: video refused in image-only gate".format(
                            entry["asset_key"]), [])

    model_id = os.getenv("SECOND_EYES_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    try:
        model = build_gemini_model()
    except Exception as e:
        return fail(4, diag_path, "PROVIDER",
                    "{}: {}".format(type(e).__name__, e), [])

    results: list[dict] = []
    for entry in entries:
        key = entry["asset_key"]
        media_path = ROOT / entry["path"]
        if media_path.suffix.lower() in VIDEO_SUFFIXES:
            return fail(2, diag_path, "CUSTODY",
                        "{}: video refused in image-only gate".format(key),
                        results)
        digest = hashlib.sha256(media_path.read_bytes()).hexdigest()
        if digest.lower() != entry["sha256"].lower():
            return fail(2, diag_path, "CUSTODY",
                        "{}: sha256 mismatch".format(key), results)
        try:
            from PIL import Image
            with Image.open(media_path) as im:
                long_edge = max(im.size)
        except Exception as e:
            return fail(2, diag_path, "CUSTODY",
                        "{}: unreadable image: {}".format(key, e), results)

        agent = Agent(model=model, system_prompt=OBSERVE_PROMPT,
                      tools=[], callback_handler=None)
        media_bytes = media_path.read_bytes()
        fmt = media_path.suffix.lstrip(".").lower()
        block = {"image": {"format": fmt, "source": {"bytes": media_bytes}}}
        try:
            result = agent([block, {"text": "Observe and reply with strict JSON."}])
        except Exception as e:
            partial = ""
            try:
                last = agent.messages[-1] if agent.messages else {}
                for blk in (last.get("content") or []):
                    if isinstance(blk, dict) and "text" in blk:
                        partial += blk["text"]
            except Exception:
                pass
            (ROOT / "outputs").mkdir(parents=True, exist_ok=True)
            return fail(4, diag_path, "PROVIDER",
                        "{}: {} (partial_chars={})".format(
                            type(e).__name__, e, len(partial)), results)
        raw = str(result).strip()
        usage = usage_snapshot(result)
        try:
            selections = parse_selection(raw)
        except RuntimeError as e:
            (ROOT / "outputs").mkdir(parents=True, exist_ok=True)
            diag = {"fixture": key, "model": model_id,
                    "prompt_version": PROMPT_VERSION, "raw": raw,
                    "usage": usage}
            diag_path.write_text(json.dumps(diag, ensure_ascii=False,
                                            indent=2), encoding="utf-8")
            return fail(3, diag_path, "SCHEMA", str(e), results)

        ref = manifest["ref_convention"]
        from runtime.vocab import FIELDS
        observed = {f: ({"value": selections[f], "ref": ref}
                        if selections[f] is not None else None)
                    for f in FIELDS}
        old_label = entry.get("old_label")
        photo = {
            "asset_key": key,
            "observed": observed,
            "old": {"colour": old_label, "item": old_label,
                    "shot": old_label},
            "signals": {"scene_claim": None, "has_people": None,
                        "long_edge": long_edge, "channel": None,
                        "sku": None},
            "signal_sources": {"long_edge": "bytes:measured"},
            "manifest": {"path": entry["path"],
                         "sha256": entry["sha256"],
                         "ref_convention": ref},
        }
        evidence_state = route({"observed": observed, "old": photo["old"]})
        item = gate({**photo, "evidence_state": evidence_state}, brief)
        item.update({
            "fixture": False,
            "model": model_id,
            "prompt_version": PROMPT_VERSION,
            "usage": usage,
            "stop_reason": usage.get("stop_reason"),
            "raw": raw,
        })
        results.append(item)
        print("{}: evidence={} verdict={} bucket={}".format(
            key, evidence_state, item["verdict"], item["bucket"]))

    from runtime.brief_gate import (BUCKET_REMAINING, BUCKET_REVIEW,
                                    BUCKET_SHORTLIST)
    summary = {
        BUCKET_SHORTLIST: sum(1 for i in results
                              if i["bucket"] == BUCKET_SHORTLIST),
        BUCKET_REVIEW: sum(1 for i in results
                           if i["bucket"] == BUCKET_REVIEW),
        BUCKET_REMAINING: sum(1 for i in results
                              if i["bucket"] == BUCKET_REMAINING),
        "total": len(results),
    }
    doc = {"complete": True, "brief_id": brief.get("brief_id"),
           "fixture": False, "model": model_id,
           "prompt_version": PROMPT_VERSION,
           "generated_at": datetime.now(timezone.utc).isoformat(),
           "model_calls": len(results), "items": results,
           "summary": summary}
    (ROOT / "outputs").mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
