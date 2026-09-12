#!/usr/bin/env python3
"""Minimal runtime pipeline — fixed brief + fixed observations, no model calls.

Chain: brief JSON -> fixed observations -> agent.loop.route (evidence
state) -> runtime.brief_gate.gate (brief verdict owns the bucket) ->
results file. Counts are computed from results, never hardcoded.

Usage (from repo root):
  python3 runtime/run_min.py --brief briefs/brief-v1.json \\
      --obs fixtures/minrun/observations.json --out outputs/minrun.json
  python3 runtime/run_min.py --no-brief \\
      --obs fixtures/minrun/observations.json --out outputs/minrun-nobrief.json
  python3 runtime/run_min.py ... --emit-preview ui/minrun/preview.html

The --emit-preview page inlines counts + cards so it renders over
file:// with no fetch. The public workroom pages are never touched.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.loop import route  # noqa: E402
from runtime.brief_gate import (BUCKET_REMAINING, BUCKET_REVIEW,  # noqa: E402
                                BUCKET_SHORTLIST)


def load_json(path: Path | None):
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def run(brief: dict | None, photos: list, fixture: bool = False) -> dict:
    items = []
    for photo in photos:
        evidence_state = route({"observed": photo.get("observed") or {},
                                "old": photo.get("old") or {}})
        # Default signal source when the input does not declare one:
        # fixed test data -> fixture:staged; anything else -> 未指定
        # (never guessed). Real runs must declare per-signal sources.
        if "signal_sources" not in photo:
            default = ("fixture:staged" if fixture else "未指定")
            photo = {**photo, "signal_sources": {
                s: default for s in (photo.get("signals") or {})}}
        # Local import keeps module import light for tests.
        from runtime.brief_gate import gate
        result = gate({**photo, "evidence_state": evidence_state}, brief)
        result["fixture"] = bool(fixture)
        items.append(result)
    summary = {
        BUCKET_SHORTLIST: sum(1 for i in items if i["bucket"] == BUCKET_SHORTLIST),
        BUCKET_REVIEW: sum(1 for i in items if i["bucket"] == BUCKET_REVIEW),
        BUCKET_REMAINING: sum(1 for i in items if i["bucket"] == BUCKET_REMAINING),
        "total": len(items),
    }
    return {
        "brief_id": (brief or {}).get("brief_id") if brief else None,
        "fixture": bool(fixture),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_calls": 0,
        "items": items,
        "summary": summary,
    }


def emit_preview(results: dict, dest: Path) -> None:
    s = results["summary"]
    cards = []
    for it in results["items"]:
        pend = ("; ".join(it["pending"]) if it["pending"] else "—")
        refs = ", ".join(
            "{}={} [{}]".format(f, (v or {}).get("value"),
                                (v or {}).get("ref"))
            for f, v in (it.get("observed") or {}).items() if v)
        srcs = ", ".join(
            "{}←{}".format(k, v)
            for k, v in (it.get("signal_sources") or {}).items())
        cards.append(
            "<li><strong>{key}</strong> · {ev} / {ver} → {bucket}<br>"
            "<small>{reason} · 待辦：{pend} · 解決人：{res}<br>"
            "觀察：{refs} · 訊號來源：{srcs}{fix}</small></li>".format(
                key=html.escape(it["asset_key"]),
                ev=html.escape(it["evidence_state"]),
                ver=html.escape(it["verdict"]),
                bucket=html.escape(it["bucket"]),
                reason=html.escape(it["reason"]),
                pend=html.escape(pend),
                res=html.escape(it["resolver"]),
                refs=html.escape(refs or "—"),
                srcs=html.escape(srcs or "—"),
                fix=" · FIXTURE" if it.get("fixture") else ""))
    dest.write_text(
        "<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">"
        "<title>Second Eyes — min-run preview</title></head><body>"
        "<h1>Min-run preview（計數由結果產生）</h1>"
        "<p>Shortlist {sl} · Needs Review {nr} · Remaining {rm} · Total {t}</p>"
        "<ul>{cards}</ul>"
        "<p><small>brief: {b} · {ts} · model calls: 0</small></p>"
        "</body></html>".format(
            sl=s["Shortlist"], nr=s["Needs Review"], rm=s["Remaining"],
            t=s["total"], cards="".join(cards),
            b=html.escape(str(results["brief_id"])),
            ts=html.escape(results["generated_at"])),
        encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", default="briefs/brief-v1.json")
    parser.add_argument("--no-brief", action="store_true")
    parser.add_argument("--obs", default="fixtures/minrun/observations.json")
    parser.add_argument("--out", default="outputs/minrun.json")
    parser.add_argument("--emit-preview", default=None)
    parser.add_argument("--manifest", default=None,
                        help="verify a small-set manifest (asset/sha/ref) "
                             "before running; aborts on mismatch")
    args = parser.parse_args()

    if args.manifest:
        from runtime.smallset import verify_manifest
        report = verify_manifest(load_json(ROOT / args.manifest), ROOT)
        if not report["ok"]:
            print("MANIFEST FAILED:")
            for e in report["errors"]:
                print(" -", e)
            return 2
        print("manifest ok:", args.manifest)

    brief = None if args.no_brief else load_json(ROOT / args.brief)
    obs_doc = load_json(ROOT / args.obs)
    results = run(brief, obs_doc["photos"],
                  fixture=bool(obs_doc.get("fixture", False)))

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(json.dumps(results["summary"], ensure_ascii=False))
    print("wrote", out_path)

    if args.emit_preview:
        dest = ROOT / args.emit_preview
        dest.parent.mkdir(parents=True, exist_ok=True)
        emit_preview(results, dest)
        print("preview", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
