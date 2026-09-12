#!/usr/bin/env python3
"""Local MVP pipeline — sealed model evidence + editor signals, no model calls.

Chain (all pure/local):
  sealed model-gate results (SHA-verified, read-only) -> recompute route
  (must equal sealed evidence_state, else stop) -> manifest verify ->
  signals.json validate -> long_edge measured from bytes ->
  brief-gate decide -> summary + coverage -> results file.

Sealed input is NEVER rewritten. Counts and coverage are computed from
decided results, never hardcoded. Public workroom pages are untouched.

Usage (from repo root):
  .venv/bin/python runtime/local_mvp.py --out outputs/local-mvp.json \\
      --emit-preview ui/minrun/preview-local.html
"""

from __future__ import annotations

import argparse
import html
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

from agent.loop import route  # noqa: E402
from runtime.brief_gate import (BUCKET_REMAINING, BUCKET_REVIEW,  # noqa: E402
                                BUCKET_SHORTLIST, gate)
from runtime.signals import validate_signals  # noqa: E402
from runtime.smallset import check_sealed_binding, verify_manifest  # noqa: E402

# Evidence comes from a TRACKED, public-safe replay of the sealed receipt,
# so a clean clone can re-derive every published number. The replay file is
# SHA-locked here; it carries the original receipt's SHA as its lineage
# anchor, and that original SHA is what results report as sealed_sha256.
# The full receipt lives under outputs/ (git-ignored); when it happens to be
# present, the replay is cross-checked against it — see check_replay_source.
REPLAY_PATH = ROOT / "fixtures/smallset/sealed-public.json"
REPLAY_SHA256 = ("6505e8b1f55f12aa569c4d48f2f735ea4acb796587902f580f6ea2e8767e53e3")
SEALED_PATH = ROOT / "outputs/smallset-gate_20260912T094617Z.json"
SEALED_SHA256 = ("15536244669f8e2b6b76f8df5a3e03dc2f2cf4f45e870716c5a759e5b3fca709")
MANIFEST_PATH = ROOT / "fixtures/smallset/manifest.json"
SIGNALS_PATH = ROOT / "fixtures/smallset/signals.json"
STUB_MARK = "mvp-stub"

import hashlib  # noqa: E402


def fail(msg: str) -> int:
    print("LOCAL-MVP STOP: {}".format(msg))
    return 2


def compute_coverage(brief: dict, items: list) -> dict:
    """Per required scene: HAVE (count + members) or MISSING. Never guessed."""
    slots = []
    for req in brief.get("required_scenes") or []:
        members = [i["asset_key"] for i in items
                   if i["bucket"] == BUCKET_SHORTLIST
                   and (i.get("signals") or {}).get("scene_claim") == req.get("scene")]
        slots.append({"slot": req.get("slot"), "scene": req.get("scene"),
                      "status": "HAVE" if members else "MISSING",
                      "count": len(members), "members": members})
    return {"slots": slots}


def load_evidence() -> tuple[dict | None, str | None]:
    """Read the tracked replay input; cross-check the receipt if present.

    Clean-clone rule: everything needed to recompute is tracked. The replay
    file is SHA-locked, and it must declare the sealed receipt it came from.
    When the original receipt happens to exist locally, the replay must be
    exactly what that receipt derives — so a doctored replay cannot survive
    on a machine that still holds the original.
    """
    if not REPLAY_PATH.is_file():
        return None, "replay input not found at {}".format(
            REPLAY_PATH.relative_to(ROOT))
    replay_bytes = REPLAY_PATH.read_bytes()
    if hashlib.sha256(replay_bytes).hexdigest() != REPLAY_SHA256:
        return None, "replay input SHA mismatch — refusing to proceed"
    replay = json.loads(replay_bytes.decode("utf-8"))
    declared = (replay.get("replay_of") or {}).get("sha256")
    if declared != SEALED_SHA256:
        return None, ("replay input declares receipt {!r}, expected "
                      "{!r}".format(declared, SEALED_SHA256))
    if SEALED_PATH.is_file():
        receipt_bytes = SEALED_PATH.read_bytes()
        if hashlib.sha256(receipt_bytes).hexdigest() != SEALED_SHA256:
            return None, "local sealed receipt SHA mismatch"
        from tools.make_replay_input import derive
        try:
            if derive(receipt_bytes)["text"] != replay_bytes.decode("utf-8"):
                return None, ("replay input is not what the local sealed "
                              "receipt derives")
        except SystemExit as e:
            return None, "replay derivation failed: {}".format(e)
    return replay, None


def run() -> tuple[dict | None, str | None]:
    """Returns (results_doc, error). Pure orchestration, no model calls."""
    sealed, error = load_evidence()
    if error:
        return None, error

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    report = verify_manifest(manifest, ROOT)
    if not report["ok"]:
        return None, "manifest: " + "; ".join(report["errors"])
    brief = json.loads((ROOT / manifest["brief"]).read_text(encoding="utf-8"))

    sealed_binding = check_sealed_binding(manifest, sealed["items"])
    if not sealed_binding["ok"]:
        return None, "sealed binding: " + "; ".join(sealed_binding["errors"])

    sealed_keys = [i["asset_key"] for i in sealed["items"]]
    sig_doc = json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))
    sig_rep = validate_signals(sig_doc, sealed_keys)
    if not sig_rep["ok"]:
        return None, "signals: " + "; ".join(sig_rep["errors"])

    items = []
    for s in sealed["items"]:
        # Determinism proof: recompute routing from sealed evidence.
        state = route({"observed": s.get("observed") or {},
                       "old": s.get("old") or {}})
        if state != s.get("evidence_state"):
            return None, "{}: route recompute {!r} != sealed {!r}".format(
                s.get("asset_key"), state, s.get("evidence_state"))
        key = s["asset_key"]
        entry = next(p for p in manifest["photos"]
                     if p["asset_key"] == key)
        media_path = ROOT / entry["path"]
        try:
            from PIL import Image
            with Image.open(media_path) as im:
                long_edge = max(im.size)
        except Exception as e:
            return None, "{}: unreadable image: {}".format(key, e)
        declared = sig_doc["signals"][key]
        signals = {**declared["signals"], "long_edge": long_edge}
        sources = {**declared.get("signal_sources", {}),
                   "long_edge": "bytes:measured"}
        photo = {"asset_key": key, "observed": s.get("observed"),
                 "old": s.get("old"), "signals": signals,
                 "signal_sources": sources,
                 "manifest": {"path": entry["path"],
                              "sha256": entry["sha256"],
                              "ref_convention": manifest["ref_convention"]}}
        item = gate({**photo, "evidence_state": state}, brief)
        # Carry sealed model provenance through untouched.
        item.update({"fixture": False, "model": s.get("model"),
                     "prompt_version": s.get("prompt_version"),
                     "usage": s.get("usage"),
                     "stop_reason": s.get("stop_reason"),
                     "raw": s.get("raw")})
        consulted = item.get("signals_used") or []
        item["stubbed"] = any(STUB_MARK in str(sources.get(c, ""))
                              for c in consulted)
        items.append(item)

    summary = {
        BUCKET_SHORTLIST: sum(1 for i in items if i["bucket"] == BUCKET_SHORTLIST),
        BUCKET_REVIEW: sum(1 for i in items if i["bucket"] == BUCKET_REVIEW),
        BUCKET_REMAINING: sum(1 for i in items if i["bucket"] == BUCKET_REMAINING),
        "total": len(items),
        "stubbed": sum(1 for i in items if i.get("stubbed")),
        # Final-gate rule: a stubbed Shortlist must not feed the public
        # workroom or any deployment. Machine-readable stop flag.
        "public_ready": not any(i["bucket"] == BUCKET_SHORTLIST
                                and i.get("stubbed") for i in items),
    }
    return {
        "brief_id": brief.get("brief_id"),
        "sealed_sha256": SEALED_SHA256,
        "fixture": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_calls": 0,
        "items": items,
        "summary": summary,
        "coverage": compute_coverage(brief, items),
    }, None


def emit_preview(results: dict, dest: Path) -> None:
    s = results["summary"]
    cov = " · ".join("{}:{} {}".format(c["slot"], c["scene"], c["status"])
                     for c in results["coverage"]["slots"])
    cards = []
    for it in results["items"]:
        pend = ("; ".join(it["pending"]) if it["pending"] else "—")
        cards.append(
            "<li><strong>{key}</strong>{stub} · {ev} / {ver} → {bucket}<br>"
            "<small>{reason} · 待辦：{pend} · 解決人：{res}</small></li>".format(
                key=html.escape(it["asset_key"]),
                stub=" · STUB" if it.get("stubbed") else "",
                ev=html.escape(it["evidence_state"]),
                ver=html.escape(it["verdict"]),
                bucket=html.escape(it["bucket"]),
                reason=html.escape(it["reason"]),
                pend=html.escape(pend),
                res=html.escape(it["resolver"])))
    dest.write_text(
        "<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">"
        "<title>Second Eyes — local MVP preview</title></head><body>"
        "<h1>Local MVP（計數與 coverage 由結果產生）</h1>"
        "<p>Shortlist {sl} · Needs Review {nr} · Remaining {rm} · Total {t}</p>"
        "<p>Coverage: {cov}</p>"
        "<ul>{cards}</ul>"
        "<p><small>brief: {b} · sealed: {sealed} · {ts} · model calls: 0</small></p>"
        "</body></html>".format(
            sl=s["Shortlist"], nr=s["Needs Review"], rm=s["Remaining"],
            t=s["total"], cov=html.escape(cov), cards="".join(cards),
            b=html.escape(str(results["brief_id"])),
            sealed=results["sealed_sha256"][:12],
            ts=html.escape(results["generated_at"])),
        encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="outputs/local-mvp.json")
    parser.add_argument("--emit-preview", default=None)
    args = parser.parse_args()
    results, error = run()
    if error:
        return fail(error)
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(json.dumps({**results["summary"],
                      "coverage": results["coverage"]},
                     ensure_ascii=False))
    print("wrote", out_path)
    if args.emit_preview:
        dest = ROOT / args.emit_preview
        dest.parent.mkdir(parents=True, exist_ok=True)
        emit_preview(results, dest)
        print("preview", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
