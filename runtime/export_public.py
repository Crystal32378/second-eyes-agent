#!/usr/bin/env python3
"""Export the sanitized public runtime payload — mechanical, no hand-filling.

Reads outputs/local-mvp.json (local, git-ignored) and writes the public
bundle under ui/runtime/:
  results.json  — allowlisted fields only (see PUBLIC_ITEM_FIELDS).
  assets/       — byte-exact copies of the 6 manifest images (SHA re-verified).
  styles.css    — byte-exact copy of the workroom stylesheet (visual continuity).

Buckets, counts, and coverage are copied from decided results, never
hand-filled. Stripped and never published: raw model responses, usage
metadata, stop reasons, model ids, prompt versions, credentials, private
paths, environment info, resolvers, undeclared signals.

Usage (from repo root):
  .venv/bin/python runtime/export_public.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR in sys.path:
    sys.path.remove(SCRIPT_DIR)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOCAL_MVP = ROOT / "outputs/local-mvp.json"
MANIFEST_PATH = ROOT / "fixtures/smallset/manifest.json"
WORKROOM = ROOT / "ui/workroom"
DEST = ROOT / "ui/runtime"

PUBLIC_ITEM_FIELDS = ("asset_key", "image", "evidence_state", "verdict",
                      "bucket", "reason", "pending", "observed",
                      "signal_sources", "manifest")

# Mechanical Chinese -> English mapping for the closed set of gate
# verdicts/reasons/pendings. Buckets and counts are computed upstream;
# this table translates fixed UI strings only. Any unmapped string
# stops the export (loud, never silent) so the public page stays
# fully English without touching the reviewed runtime.
VERDICT_EN = {"符合": "Match", "明確不符": "Mismatch", "證據不足": "Insufficient evidence"}

REASON_EN = {
    "缺 brief：無核對基準": "No brief: nothing to check against",
    "缺證據：無有效觀察（含 ref）": "Insufficient evidence: no valid observation (with ref)",
    "明確不符：brief 要求無人物": "Mismatch: the brief requires no people",
    "證據不足：缺人物訊號，無法核對無人物約束":
        "Insufficient evidence: missing person signal, cannot check the no-people rule",
    "證據不足：缺解析度訊號，無法核對最小邊":
        "Insufficient evidence: missing resolution signal, cannot check the minimum edge",
    "明確不符：解析度低於 brief 下限": "Mismatch: resolution below the brief minimum",
    "證據不足：缺通路訊號，無法核對通路":
        "Insufficient evidence: missing channel signal, cannot check the channel",
    "明確不符：通路非 brief 允許": "Mismatch: channel not allowed by the brief",
    "證據不足：缺 SKU，無法核對上架事實":
        "Insufficient evidence: missing SKU, cannot check live facts",
    "明確不符：SKU 非本次上架": "Mismatch: SKU is not live in this round",
    "證據不足：無法判定場景槽位": "Insufficient evidence: scene slot cannot be determined",
    "明確不符：場景非本次需求": "Mismatch: scene is not required this round",
    "符合：場景與硬約束皆通過": "Match: scene and hard constraints all pass",
}

PENDING_EN = {
    "提供本次 brief": "Provide this round's brief",
    "補拍或補證據 ref": "Re-shoot or attach an evidence ref",
    "由人工判定哪筆紀錄有誤": "Have a human judge which record is wrong",
    "補人物訊號": "Provide a person signal",
    "修正人物訊號為 boolean": "Fix the person signal to a boolean",
    "補長邊像素數": "Provide the long-edge pixel count",
    "補通路": "Provide the channel",
    "補 SKU": "Provide the SKU",
    "由人工指派場景": "Have a human assign the scene",
    "補訊號來源": "Provide signal sources",
}


def translate_reason(reason: str) -> str:
    if reason in REASON_EN:
        return REASON_EN[reason]
    if reason.startswith("衝突：舊標籤與所見不符（") and reason.endswith("）"):
        inner = reason[len("衝突：舊標籤與所見不符（"):-1].replace(
            " 欄位", " field")
        return ("Conflict: prior label disagrees with what is seen "
                "({})".format(inner))
    if reason.startswith("資料錯誤：has_people 非 boolean（") and reason.endswith("），不得通過"):
        typename = reason[len("資料錯誤：has_people 非 boolean（"):-
                          len("），不得通過")]
        return ("Data error: has_people is not a boolean ({}), "
                "cannot pass".format(typename))
    if reason.startswith("證據不足：缺訊號來源（") and reason.endswith("）"):
        inner = reason[len("證據不足：缺訊號來源（"):-1]
        return "Insufficient evidence: missing signal source ({})".format(inner)
    raise KeyError("unmapped reason: {!r}".format(reason))

# Anything containing these (case-insensitive, anywhere in results.json)
# fails the built-in sanitization audit.
FORBIDDEN_MARKERS = ("raw", "usage", "stop_reason", "prompt_version",
                     "GEMINI", "GOOGLE_", "AKIA", "ASIA", "BEGIN PRIVATE",
                     "/Users/", "/home/", ".pem", "amazon.nova",
                     "mvp-stub")


def fail(msg: str) -> int:
    print("EXPORT STOP: {}".format(msg))
    return 2


def main() -> int:
    local = json.loads(LOCAL_MVP.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_key = {p["asset_key"]: p for p in manifest["photos"]}

    if not local.get("summary", {}).get("public_ready", False):
        return fail("local MVP summary.public_ready is not true — refusing "
                    "to publish a stubbed batch")

    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "assets").mkdir(parents=True, exist_ok=True)

    items = []
    for src in local["items"]:
        key = src["asset_key"]
        if key not in by_key:
            return fail("item not in manifest: {}".format(key))
        src_file = WORKROOM / "assets" / (by_key[key]["path"].split("/")[-1])
        if not src_file.is_file():
            return fail("workroom asset missing: {}".format(src_file))
        digest = hashlib.sha256(src_file.read_bytes()).hexdigest()
        if digest.lower() != by_key[key]["sha256"].lower():
            return fail("asset SHA mismatch: {}".format(key))
        dest_file = DEST / "assets" / src_file.name
        shutil.copyfile(src_file, dest_file)
        if hashlib.sha256(dest_file.read_bytes()).hexdigest().lower() != digest.lower():
            return fail("copy verification failed: {}".format(key))
        try:
            verdict_en = VERDICT_EN[src["verdict"]]
            reason_en = translate_reason(src["reason"])
            pending_en = [PENDING_EN[p] for p in src["pending"]]
        except KeyError as e:
            return fail("unmapped UI string for {}: {}".format(key, e))
        # Publish only consulted signal sources: provenance behind the
        # published decision (signals_used from the local MVP), so
        # never-consulted stub declarations stay out of the public bundle.
        consulted = src.get("signals_used") or []
        pub_sources = {s: src["signal_sources"][s] for s in consulted
                       if s in (src.get("signal_sources") or {})}
        item = {
            "asset_key": key,
            "image": "assets/{}".format(src_file.name),
            "evidence_state": src["evidence_state"],
            "verdict": verdict_en,
            "bucket": src["bucket"],
            "reason": reason_en,
            "pending": pending_en,
            "observed": src["observed"],
            "signal_sources": pub_sources,
            "manifest": {"sha256": by_key[key]["sha256"],
                         "ref_convention": manifest["ref_convention"]},
        }
        for f in PUBLIC_ITEM_FIELDS:
            if f not in item:
                return fail("{}: missing public field {}".format(key, f))
        items.append(item)

    payload = {
        "page": "verified 6-image runtime",
        "brief_id": local["brief_id"],
        "sealed_sha256": local["sealed_sha256"],
        "summary": {k: local["summary"][k] for k in
                    ("Shortlist", "Needs Review", "Remaining", "total")},
        "coverage": local["coverage"],
        "items": items,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    lowered = text.lower()
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in lowered:
            return fail("sanitization audit hit: {!r}".format(marker))

    css_src = WORKROOM / "styles.css"
    css_dest = DEST / "styles.css"
    shutil.copyfile(css_src, css_dest)
    if css_src.read_bytes() != css_dest.read_bytes():
        return fail("stylesheet copy mismatch")

    (DEST / "results.json").write_text(text, encoding="utf-8")
    print("exported {} items to {}".format(len(items), DEST / "results.json"))
    print("summary:", json.dumps(payload["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
