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

#: Marker for "no provenance declared". Treated as missing everywhere.
UNRESOLVED_SOURCE = "未指定"


def _duplicates(keys: list) -> list:
    seen, dupes = set(), []
    for k in keys:
        if k in seen and k not in dupes:
            dupes.append(k)
        seen.add(k)
    return dupes


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


def check_binding(manifest: dict, photos: list, fixture: bool) -> dict:
    """Bind manifest entries to observations, one to one.

    Custody gate: proves "that evidence belongs to that photo" before any
    model call may use it. Failures (exit 2 in run_min, nothing written):
    - fixture:true observations in real --manifest mode are rejected.
    - asset_key sets must match exactly with equal counts: missing,
      extra, or duplicate keys fail.
    - every attached observation ref must start with the manifest's
      ref_convention (the convention alone being non-empty is not enough).
    Returns {"ok", "errors"}.
    """
    errors: list[str] = []
    if fixture:
        errors.append("real --manifest mode rejects fixture:true observations")
    m_photos = (manifest or {}).get("photos") or []
    m_keys = [p.get("asset_key") for p in m_photos]
    o_keys = [p.get("asset_key") for p in photos]
    for dup in _duplicates(m_keys):
        errors.append("manifest duplicate asset_key: {}".format(dup))
    for dup in _duplicates(o_keys):
        errors.append("observations duplicate asset_key: {}".format(dup))
    if len(photos) != len(m_photos):
        errors.append("count mismatch: manifest {} vs observations {}".format(
            len(m_photos), len(photos)))
    for k in sorted(set(m_keys) - set(o_keys)):
        errors.append("missing in observations: {}".format(k))
    for k in sorted(set(o_keys) - set(m_keys)):
        errors.append("not in manifest: {}".format(k))
    convention = (manifest or {}).get("ref_convention")
    if not convention:
        errors.append("cannot check refs: manifest missing ref_convention")
    else:
        for p in photos:
            key = p.get("asset_key", "?")
            for field, sel in (p.get("observed") or {}).items():
                if (isinstance(sel, dict) and sel.get("value")
                        and sel.get("ref")
                        and not str(sel["ref"]).startswith(convention)):
                    errors.append(
                        "{}: ref {!r} does not match convention {!r}".format(
                            key, sel["ref"], convention))
    return {"ok": not errors, "errors": errors}
