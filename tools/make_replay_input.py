#!/usr/bin/env python3
"""Derive the tracked, public-safe replay input from the sealed receipt.

The sealed model-gate receipt lives under outputs/, which is git-ignored,
so a clean clone cannot re-derive anything from it. This script strips the
receipt down to the fields the local MVP actually needs to recompute, and
writes them to a TRACKED file that carries the original receipt's SHA as
its lineage anchor.

Kept per item (and nothing else):
  asset_key        which photo
  evidence_state   the sealed routing, re-derived and compared on every run
  observed         the model's observations (values + refs)
  old              the prior label, as expanded from the manifest
  manifest         path / sha256 / ref_convention — WITHOUT this,
                   check_sealed_binding cannot detect a manifest swap,
                   so dropping it would silently remove a safety check
  model,
  prompt_version   which model produced the evidence (provenance)

Never carried: raw model text, usage metadata, stop reasons, and the
downstream verdict/bucket/reason/pending/resolver/signals — those are
RECOMPUTED from the brief, never replayed, so shipping them would only
invite trusting a copy instead of the computation.

Usage (from repo root):
  python3 tools/make_replay_input.py
  python3 tools/make_replay_input.py --check   # verify, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "outputs/smallset-gate_20260912T094617Z.json"
RECEIPT_SHA256 = "15536244669f8e2b6b76f8df5a3e03dc2f2cf4f45e870716c5a759e5b3fca709"
REPLAY = ROOT / "fixtures/smallset/sealed-public.json"

ITEM_FIELDS = ("asset_key", "evidence_state", "observed", "old", "manifest",
               "model", "prompt_version")
BANNED = ("raw", "usage", "stop_reason")


def derive(receipt_bytes: bytes) -> dict:
    digest = hashlib.sha256(receipt_bytes).hexdigest()
    if digest != RECEIPT_SHA256:
        raise SystemExit("REPLAY STOP: receipt SHA {} != pinned {}".format(
            digest, RECEIPT_SHA256))
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    items = []
    for s in receipt["items"]:
        item = {f: s.get(f) for f in ITEM_FIELDS}
        for f in ITEM_FIELDS:
            if item[f] is None:
                raise SystemExit("REPLAY STOP: {} missing {}".format(
                    s.get("asset_key"), f))
        items.append(item)
    doc = {
        "note": ("Public replay input: the minimum needed to recompute the "
                 "local MVP in a clean clone. Derived mechanically from the "
                 "sealed receipt by tools/make_replay_input.py — never "
                 "hand-edited. Verdicts and buckets are NOT here; they are "
                 "recomputed from the brief."),
        "replay_of": {"receipt": str(RECEIPT.relative_to(ROOT)),
                      "sha256": RECEIPT_SHA256},
        "brief_id": receipt["brief_id"],
        "model_calls": 0,
        "items": items,
    }
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    lowered = text.lower()
    for marker in BANNED + ("/users/", "/home/", "akia", "asia",
                            "begin private", ".pem"):
        if marker in lowered:
            raise SystemExit("REPLAY STOP: banned marker {!r}".format(marker))
    return {"text": text, "doc": doc}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not RECEIPT.is_file():
        print("REPLAY STOP: sealed receipt not present at {} — this script "
              "runs only where the original receipt exists".format(
                  RECEIPT.relative_to(ROOT)))
        return 2
    built = derive(RECEIPT.read_bytes())
    if args.check:
        if not REPLAY.is_file():
            print("REPLAY STOP: {} missing".format(REPLAY.relative_to(ROOT)))
            return 2
        current = REPLAY.read_text(encoding="utf-8")
        if current != built["text"]:
            print("REPLAY STOP: {} is not what the receipt derives".format(
                REPLAY.relative_to(ROOT)))
            return 2
        print("replay input matches the sealed receipt")
        return 0
    REPLAY.write_text(built["text"], encoding="utf-8")
    print("wrote {} ({} items)".format(REPLAY.relative_to(ROOT),
                                       len(built["doc"]["items"])))
    print("replay sha256:", hashlib.sha256(
        built["text"].encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
