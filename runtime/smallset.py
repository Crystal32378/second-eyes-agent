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
                        and str(sel["ref"]) != convention):
                    errors.append(
                        "{}: ref {!r} != convention {!r}".format(
                            key, sel["ref"], convention))
    return {"ok": not errors, "errors": errors}


def apply_manifest(manifest: dict, photos: list) -> list:
    """Attach manifest custody to photos and mechanically inject old labels.

    `old` is NEVER taken from observations in manifest mode: every photo's
    old {colour,item,shot} is built from its manifest entry's old_label
    (same convention as run_synthetic_gemini.py), so smuggling a different
    old label cannot change CLEAR/CONFLICT/NEW routing. Call only after
    check_binding passed (exact key match guaranteed).
    """
    by_key = {p["asset_key"]: p for p in manifest["photos"]}
    out = []
    for p in photos:
        m = by_key[p["asset_key"]]
        old_label = m.get("old_label")
        out.append({**p,
                    "old": {"colour": old_label,
                            "item": old_label,
                            "shot": old_label},
                    "manifest": {
                        "path": m["path"],
                        "sha256": m["sha256"],
                        "ref_convention": manifest["ref_convention"],
                    }})
    return out


def check_sealed_binding(manifest: dict, sealed_items: list) -> dict:
    """Bind sealed model-gate items to the CURRENT manifest, per item.

    The sealed file records the manifest {asset_key/path/sha256/
    ref_convention} each evidence was produced against. If the manifest
    has since changed for the same asset_key (e.g. swapped to another
    legal file + SHA — verify_manifest alone would still pass), the
    evidence no longer belongs to that photo and must stop.
    Also checks: sealed old == mechanical expansion of the current
    manifest old_label; key sets equal with equal counts and no
    duplicates on either side.
    Returns {"ok", "errors"}.
    """
    errors: list[str] = []
    m_photos = (manifest or {}).get("photos") or []
    m_keys = [p.get("asset_key") for p in m_photos]
    s_keys = [i.get("asset_key") for i in sealed_items]
    for dup in _duplicates(m_keys):
        errors.append("manifest duplicate asset_key: {}".format(dup))
    for dup in _duplicates(s_keys):
        errors.append("sealed duplicate asset_key: {}".format(dup))
    if len(sealed_items) != len(m_photos):
        errors.append("count mismatch: manifest {} vs sealed {}".format(
            len(m_photos), len(sealed_items)))
    for k in sorted(set(m_keys) - set(s_keys)):
        errors.append("missing in sealed: {}".format(k))
    for k in sorted(set(s_keys) - set(m_keys)):
        errors.append("sealed item not in manifest: {}".format(k))
    by_key = {p["asset_key"]: p for p in m_photos}
    convention = (manifest or {}).get("ref_convention")
    for item in sealed_items:
        key = item.get("asset_key", "?")
        if key not in by_key:
            continue
        m = by_key[key]
        sealed_manifest = item.get("manifest") or {}
        for field in ("path", "sha256", "ref_convention"):
            expected = m[field] if field != "ref_convention" else convention
            if sealed_manifest.get(field) != expected:
                errors.append(
                    "{}: sealed manifest {!r} {!r} != current {!r}".format(
                        key, field, sealed_manifest.get(field), expected))
        old_label = m.get("old_label")
        expected_old = {"colour": old_label, "item": old_label,
                        "shot": old_label}
        if (item.get("old") or {}) != expected_old:
            errors.append(
                "{}: sealed old != manifest old_label expansion".format(key))
    return {"ok": not errors, "errors": errors}
