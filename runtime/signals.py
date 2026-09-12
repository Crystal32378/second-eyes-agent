"""Editor-declared signal validation (Phase 2, local MVP).

signals.json maps asset_key -> {signals, signal_sources}. Rules:
- keys must equal the sealed result asset keys exactly (no missing,
  extra, or duplicates — checked by the caller against sealed items).
- signals: scene_claim (required-scene name or null), has_people
  (bool or null), channel (str or null), sku (str or null).
  long_edge is FORBIDDEN here (pipeline measures it from bytes).
- signal_sources: every NON-NULL signal must have a strict source
  (stripped non-empty string, not 未指定). Null signals need no source.
  Stub sources (editor:mvp-stub...) are allowed but flagged downstream.
"""

from __future__ import annotations

ALLOWED_KEYS = ("scene_claim", "has_people", "channel", "sku")
UNRESOLVED = "未指定"


def validate_signals(doc: dict, asset_keys: list) -> dict:
    """Returns {"ok", "errors"}. Pure, no I/O."""
    errors: list[str] = []
    table = (doc or {}).get("signals")
    if not isinstance(table, dict):
        return {"ok": False, "errors": ["signals.json missing signals table"]}
    if set(table) != set(asset_keys):
        for k in sorted(set(asset_keys) - set(table)):
            errors.append("missing signals for: {}".format(k))
        for k in sorted(set(table) - set(asset_keys)):
            errors.append("signals not in sealed results: {}".format(k))
    for key, entry in table.items():
        if not isinstance(entry, dict):
            errors.append("{}: entry must be an object".format(key))
            continue
        signals = entry.get("signals") or {}
        sources = entry.get("signal_sources") or {}
        for s in signals:
            if s not in ALLOWED_KEYS:
                errors.append("{}: forbidden signal key: {}".format(key, s))
        sc, hp, ch, sku = (signals.get("scene_claim"),
                           signals.get("has_people"),
                           signals.get("channel"), signals.get("sku"))
        if sc is not None and not isinstance(sc, str):
            errors.append("{}: scene_claim must be str or null".format(key))
        if hp is not None and not isinstance(hp, bool):
            errors.append("{}: has_people must be bool or null".format(key))
        for name, val in (("channel", ch), ("sku", sku)):
            if val is not None and not isinstance(val, str):
                errors.append("{}: {} must be str or null".format(key, name))
        for name, val in signals.items():
            if val is None:
                continue
            src = sources.get(name)
            if (not isinstance(src, str) or not src.strip()
                    or src.strip() == UNRESOLVED):
                errors.append(
                    "{}: declared signal {!r} lacks a strict source".format(
                        key, name))
    return {"ok": not errors, "errors": errors}
