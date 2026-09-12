"""Small-set manifest verification for the future gated real-image test.

Checks every manifest entry's asset key, file presence, sha256, and the
top-level ref convention BEFORE any model call may use it. Pure local
file checks, no model calls, no network.

Manifest contract (fixtures/smallset/manifest.json):
  top-level: {"brief", "ref_convention", "photos": [
    {"asset_key", "path" (repo-relative), "sha256", "old_label"}]}
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REQUIRED_ENTRY_KEYS = ("asset_key", "path", "sha256", "old_label")


def verify_manifest(manifest: dict, root: Path) -> dict:
    """Verify asset/sha/ref-convention. Returns {"ok", "entries", "errors"}."""
    entries = []
    errors: list[str] = []
    ref_convention = (manifest or {}).get("ref_convention")
    if not ref_convention:
        errors.append("manifest missing ref_convention")
    for i, entry in enumerate((manifest or {}).get("photos") or []):
        key = entry.get("asset_key") or "#{}".format(i)
        item = {"asset_key": key, "ok": True, "errors": []}
        for k in REQUIRED_ENTRY_KEYS:
            if k not in entry or entry[k] is None:
                item["errors"].append("missing key: {}".format(k))
        rel = entry.get("path")
        if rel:
            target = root / rel
            if not target.is_file():
                item["errors"].append("file not found: {}".format(rel))
            elif entry.get("sha256"):
                digest = hashlib.sha256(target.read_bytes()).hexdigest()
                if digest.lower() != entry["sha256"].lower():
                    item["errors"].append(
                        "sha256 mismatch: {}".format(rel))
        item["ok"] = not item["errors"]
        if not item["ok"]:
            errors.append("{}: {}".format(key, "; ".join(item["errors"])))
        entries.append(item)
    return {"ok": not errors, "ref_convention": ref_convention,
            "entries": entries, "errors": errors}
