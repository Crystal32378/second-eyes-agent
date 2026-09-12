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


def run(brief: dict | None, photos: list) -> dict:
    items = []
    for photo in photos:
        evidence_state = route({"observed": photo.get("observed") or {},
                                "old": photo.get("old") or {}})
        # Local import keeps module import light for tests.
        from runtime.brief_gate import gate
        result = gate({**photo, "evidence_state": evidence_state}, brief)
        items.append(result)
    summary = {
        BUCKET_SHORTLIST: sum(1 for i in items if i["bucket"] == BUCKET_SHORTLIST),
        BUCKET_REVIEW: sum(1 for i in items if i["bucket"] == BUCKET_REVIEW),
        BUCKET_REMAINING: sum(1 for i in items if i["bucket"] == BUCKET_REMAINING),
        "total": len(items),
    }
    return {
        "brief_id": (brief or {}).get("brief_id") if brief else None,
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
        cards.append(
            "<li><strong>{key}</strong> · {ev} / {ver} → {bucket}<br>"
            "<small>{reason} · 待辦：{pend} · 解決人：{res}</small></li>".format(
                key=html.escape(it["asset_key"]),
                ev=html.escape(it["evidence_state"]),
                ver=html.escape(it["verdict"]),
                bucket=html.escape(it["bucket"]),
                reason=html.escape(it["reason"]),
                pend=html.escape(pend),
                res=html.escape(it["resolver"])))
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
    args = parser.parse_args()

    brief = None if args.no_brief else load_json(ROOT / args.brief)
    obs_doc = load_json(ROOT / args.obs)
    results = run(brief, obs_doc["photos"])

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
