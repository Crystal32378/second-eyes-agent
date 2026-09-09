"""Batch A reader hash gate — membership + bytes verification ONLY.

Reads (read-only):
  - sample_manifest.csv rows sample_order 1–60
  - source bytes Desktop/Brand Image/<rel_path>
Verifies per-row SHA-256 before ANY agent processing.
Yields: asset_key (rel_path), kind, sha256, canonical pointers
  (resolved separately from registry join at run time).

NEVER reads: observations.jsonl, inventory, summaries, run logs.
"""

import csv
import hashlib
import os

# Corpus locations are private evaluation infrastructure and MUST NOT be
# hardcoded: configure via environment. Defaults are inert placeholders.
MANIFEST = os.getenv("SECOND_EYES_MANIFEST", "")
SOURCE_ROOT = os.getenv("SECOND_EYES_SOURCE_ROOT", "")
EXPECTED_MANIFEST_SHA256 = "653e987cbaf7fd6df3466b8dececdc95bdb872ab1f2b644cfafb68c0f96e8563"


def manifest_rows():
    with open(MANIFEST, newline="") as f:
        for r in csv.DictReader(f):
            if 1 <= int(r["sample_order"]) <= 60:
                yield r


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1024 * 1024), b""):
            h.update(ch)
    return h.hexdigest()


def gate_batch_a():
    """Verify manifest SHA + 60/60 source bytes. Returns list of gated items.
    Raises on any mismatch. No semantic classification here.
    Requires SECOND_EYES_MANIFEST and SECOND_EYES_SOURCE_ROOT."""
    if not MANIFEST or not SOURCE_ROOT:
        raise RuntimeError(
            "Batch A corpus not configured: set SECOND_EYES_MANIFEST and "
            "SECOND_EYES_SOURCE_ROOT (private evaluation infrastructure).")
    h = sha256_file(MANIFEST)
    if h.lower() != EXPECTED_MANIFEST_SHA256.lower():
        raise RuntimeError(f"manifest SHA mismatch: {h}")
    items = []
    for r in manifest_rows():
        fp = os.path.join(SOURCE_ROOT, r["rel_path"])
        if not os.path.exists(fp):
            raise RuntimeError(f"missing source byte: {r['rel_path']}")
        digest = sha256_file(fp)
        if digest.lower() != r["sha256"].lower():
            raise RuntimeError(f"byte SHA mismatch: {r['rel_path']}")
        items.append({
            "asset_key": r["rel_path"],
            "kind": r["kind"],
            "sha256": r["sha256"],
            "sample_order": int(r["sample_order"]),
            "collection": r["collection"],
        })
    if len(items) != 60:
        raise RuntimeError(f"membership drift: {len(items)} != 60")
    return items
