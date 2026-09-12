#!/usr/bin/env python3
"""Export the sanitized public runtime payload — mechanical, no hand-filling.

Lineage rule: the published bundle is derived from a LOCAL MVP RECOMPUTED
here from the SHA-sealed model-gate input (runtime.local_mvp.run), never
from the on-disk outputs/local-mvp.json, which is git-ignored and locally
editable. If that file is present it must agree item-by-item with the
recompute; any divergence stops the export. Nothing is written until every
check passes, so a stopped export leaves no partial bundle behind.

Writes the public bundle under ui/runtime/:
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
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR in sys.path:
    sys.path.remove(SCRIPT_DIR)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.local_mvp import run as local_mvp_run  # noqa: E402

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


# Fields that decide what the public page says. The on-disk local MVP may
# differ from the recompute ONLY in fields nobody publishes (generated_at).
# Anything in this projection is lineage-bearing and must match exactly.
LINEAGE_TOP = ("brief_id", "sealed_sha256", "coverage")
LINEAGE_SUMMARY = ("Shortlist", "Needs Review", "Remaining", "total",
                   "stubbed", "public_ready")
LINEAGE_ITEM = ("asset_key", "evidence_state", "verdict", "bucket", "reason",
                "pending", "observed", "signals", "signal_sources",
                "signals_used", "resolver", "stubbed", "manifest")


def lineage_projection(doc: dict) -> dict:
    """The publish-relevant slice of a local MVP document."""
    return {
        "top": {k: doc.get(k) for k in LINEAGE_TOP},
        "summary": {k: (doc.get("summary") or {}).get(k)
                    for k in LINEAGE_SUMMARY},
        "items": [{k: it.get(k) for k in LINEAGE_ITEM}
                  for it in doc.get("items") or []],
    }


def lineage_diff(recomputed: dict, on_disk: dict) -> list:
    """Item-by-item divergence list; empty means the file is trustworthy."""
    a, b = lineage_projection(recomputed), lineage_projection(on_disk)
    diffs = []
    for k in LINEAGE_TOP:
        if a["top"][k] != b["top"][k]:
            diffs.append("top-level {!r} differs".format(k))
    for k in LINEAGE_SUMMARY:
        if a["summary"][k] != b["summary"][k]:
            diffs.append("summary {!r}: recomputed {!r} != file {!r}".format(
                k, a["summary"][k], b["summary"][k]))
    if len(a["items"]) != len(b["items"]):
        diffs.append("item count: recomputed {} != file {}".format(
            len(a["items"]), len(b["items"])))
    else:
        for x, y in zip(a["items"], b["items"]):
            for k in LINEAGE_ITEM:
                if x.get(k) != y.get(k):
                    diffs.append("{}: {!r} recomputed {!r} != file {!r}".format(
                        x.get("asset_key") or y.get("asset_key"), k,
                        x.get(k), y.get(k)))
    return diffs


def load_verified_local() -> tuple[dict | None, str | None]:
    """Recompute the local MVP from sealed input; cross-check the file.

    The recompute is the source of truth. outputs/local-mvp.json is
    advisory only: when present it must agree on every lineage-bearing
    field, otherwise the export stops rather than publishing a payload
    whose provenance cannot be re-derived.
    """
    recomputed, error = local_mvp_run()
    if error:
        return None, "local MVP recompute failed: {}".format(error)
    if LOCAL_MVP.is_file():
        try:
            on_disk = json.loads(LOCAL_MVP.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            return None, "outputs/local-mvp.json unreadable: {}".format(e)
        diffs = lineage_diff(recomputed, on_disk)
        if diffs:
            return None, ("outputs/local-mvp.json diverges from the sealed "
                          "recompute ({} difference(s)); first: {}".format(
                              len(diffs), diffs[0]))
    return recomputed, None


def main() -> int:
    local, lineage_error = load_verified_local()
    if lineage_error:
        return fail(lineage_error)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_key = {p["asset_key"]: p for p in manifest["photos"]}

    if not local.get("summary", {}).get("public_ready", False):
        return fail("local MVP summary.public_ready is not true — refusing "
                    "to publish a stubbed batch")

    # Everything is built in a staging directory on the same filesystem and
    # moved into place only after every check passes, so an EXPORT STOP can
    # never leave a half-written bundle (or a stale asset) behind.
    stage_parent = DEST.parent
    stage_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".runtime-stage-", dir=stage_parent))
    try:
        return build(local, manifest, by_key, stage)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def build(local: dict, manifest: dict, by_key: dict, stage: Path) -> int:
    (stage / "assets").mkdir(parents=True, exist_ok=True)

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
        dest_file = stage / "assets" / src_file.name
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
        "page": "recorded 6-image run (static viewer)",
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
    css_dest = stage / "styles.css"
    shutil.copyfile(css_src, css_dest)
    if css_src.read_bytes() != css_dest.read_bytes():
        return fail("stylesheet copy mismatch")

    (stage / "results.json").write_text(text, encoding="utf-8")

    # Commit: index.html is authored, not generated, so it is preserved
    # across the swap; every generated file comes from the staging dir.
    index_html = DEST / "index.html"
    keep = index_html.read_bytes() if index_html.is_file() else None
    DEST.mkdir(parents=True, exist_ok=True)
    for name in ("results.json", "styles.css"):
        shutil.copyfile(stage / name, DEST / name)
    assets_dest = DEST / "assets"
    assets_dest.mkdir(parents=True, exist_ok=True)
    staged_assets = {f.name for f in (stage / "assets").iterdir()}
    for f in sorted((stage / "assets").iterdir()):
        shutil.copyfile(f, assets_dest / f.name)
    for f in sorted(assets_dest.iterdir()):
        if f.name not in staged_assets:
            f.unlink()
    if keep is not None and index_html.read_bytes() != keep:
        return fail("viewer index.html was modified by the export")

    print("exported {} items to {}".format(len(items), DEST / "results.json"))
    print("summary:", json.dumps(payload["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
