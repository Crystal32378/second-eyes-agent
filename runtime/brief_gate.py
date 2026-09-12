"""Brief-gate: brief verdict owns the publishing bucket.

Stage 1 (`agent.loop.route`) outputs a per-photo evidence state only
(CLEAR / CONFLICT / UNKNOWN / NEW) from observed-vs-old on frozen vocab.
It decides NO bucket.

Stage 2 (this module) assigns the bucket from the brief verdict, which is
exactly one of: 符合 / 明確不符 / 證據不足 — evaluated against the fixed
brief (`briefs/brief-v1.json`): required scenes, hard constraints,
channel fit, supplied facts.

Rules:
- Missing brief -> 證據不足 -> Needs Review (no brief = no basis).
- Missing evidence (UNKNOWN with nothing valid observed) -> 證據不足
  -> Needs Review. Only brief-related blocking missing/conflict blocks
  candidacy; anything else proceeds to brief checks.
- CONFLICT on a brief-relevant field -> 證據不足 -> Needs Review.
  CONFLICT on an irrelevant field does NOT block; brief checks decide.
- Brief checks (constraints, then scene) decide the verdict:
  符合 -> Shortlist, 明確不符 -> Remaining, 證據不足 -> Needs Review.
  Every evidence state can reach every verdict path, including
  CLEAR + 證據不足 -> Needs Review (e.g. constraint signal absent).
- Resolver: `brief["resolvers"][key]` when present, else "未指定".
  Never guessed.
- Signal sources: every signal actually consulted for the verdict must
  have a non-empty, non-"未指定" source in `photo["signal_sources"]`.
  A consulted signal without source stops at Needs Review — nothing
  unsourced may enter Shortlist (or Remaining on unsourced grounds).
- Manifest: `photo["manifest"]` ({path, sha256, ref_convention}) is
  passed through untouched when the runner bound the photo to a
  manifest entry, so results prove which file the evidence came from.
"""

from __future__ import annotations

from runtime.vocab import FIELDS, normalize, scan_old

BUCKET_SHORTLIST = "Shortlist"
BUCKET_REVIEW = "Needs Review"
BUCKET_REMAINING = "Remaining"

VERDICT_MATCH = "符合"
VERDICT_MISMATCH = "明確不符"
VERDICT_INSUFFICIENT = "證據不足"

UNRESOLVED = "未指定"


def _observed_tokens(observed: dict) -> dict:
    """Valid observed tokens only (in-vocab + non-empty ref)."""
    out = {}
    for f in FIELDS:
        raw = (observed or {}).get(f)
        if isinstance(raw, dict):
            tok = normalize(f, raw.get("value"))
            out[f] = tok if (tok is not None and raw.get("ref")) else None
        else:
            out[f] = None
    return out


def _conflict_fields(observed: dict, old: dict) -> list:
    """Fields where observed and old are both comparable but unequal."""
    obs = _observed_tokens(observed)
    prev = {f: scan_old(f, (old or {}).get(f)) for f in FIELDS}
    return [f for f in FIELDS
            if obs[f] is not None and prev[f] is not None
            and obs[f] != prev[f]]


def _resolver(brief: dict, key: str) -> str:
    return ((brief or {}).get("resolvers") or {}).get(key) or UNRESOLVED


def gate(photo: dict, brief: dict | None) -> dict:
    """Run the brief-gate for one photo.

    photo: {asset_key, evidence_state, observed, old, signals}.
    signals: {scene_claim, has_people, long_edge, channel, sku}.
    brief: parsed brief-v1 dict, or None for the missing-brief scenario.

    Returns {asset_key, evidence_state, verdict, bucket, reason,
    pending, resolver, observed, signals, signal_sources, manifest}.
    Pure function, no model call, no I/O.
    """
    asset_key = photo.get("asset_key", "")
    evidence_state = photo.get("evidence_state", "UNKNOWN")
    observed = photo.get("observed") or {}
    old = photo.get("old") or {}
    signals = photo.get("signals") or {}
    sources = photo.get("signal_sources") or {}
    used: list[str] = []

    def _sourced(name: str) -> bool:
        src = sources.get(name)
        return bool(src) and src != UNRESOLVED

    def out(verdict, bucket, reason, pending, resolver_key):
        # Custody: a consulted signal without source cannot decide.
        # Anything not already stopped for review stops here instead —
        # never Shortlist (or Remaining) on unsourced grounds.
        if bucket != BUCKET_REVIEW:
            missing = [s for s in used if not _sourced(s)]
            if missing:
                return {
                    "asset_key": asset_key,
                    "evidence_state": evidence_state,
                    "verdict": VERDICT_INSUFFICIENT,
                    "bucket": BUCKET_REVIEW,
                    "reason": "證據不足：缺訊號來源（{}）".format(
                        "、".join(missing)),
                    "pending": ["補訊號來源"],
                    "resolver": _resolver(brief, "evidence"),
                    "observed": observed,
                    "signals": signals,
                    "signal_sources": dict(sources),
                    "manifest": photo.get("manifest"),
                }
        return {
            "asset_key": asset_key,
            "evidence_state": evidence_state,
            "verdict": verdict,
            "bucket": bucket,
            "reason": reason,
            "pending": list(pending),
            "resolver": _resolver(brief, resolver_key),
            # Traceability: keep the observation refs and the signals
            # (with their sources) that the brief verdict was based on,
            # so the viewer can show why a photo was bucketed.
            "observed": observed,
            "signals": signals,
            "signal_sources": dict(sources),
            "manifest": photo.get("manifest"),
        }

    # 1. Missing brief: no clearance basis, everything needs review.
    if brief is None:
        return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                   "缺 brief：無核對基準",
                   ["提供本次 brief"], "brief")

    relevant = set(brief.get("relevant_fields") or list(FIELDS))
    obs = _observed_tokens(observed)

    # 2. Missing evidence blocks: nothing valid observed.
    if evidence_state == "UNKNOWN" and not any(obs.values()):
        return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                   "缺證據：無有效觀察（含 ref）",
                   ["補拍或補證據 ref"], "evidence")

    # 3. Brief-related conflict blocks; irrelevant-field conflict does not.
    if evidence_state == "CONFLICT":
        fields = [f for f in _conflict_fields(observed, old)
                  if f in relevant]
        if fields:
            return out(
                VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                "衝突：舊標籤與所見不符（{}）".format(
                    "、".join(f + " 欄位" for f in fields)),
                ["由人工判定哪筆紀錄有誤"], "conflict")

    hard = (brief.get("hard_constraints") or {})
    facts = (brief.get("supplied_facts") or {})
    required = {(s.get("slot"), s.get("scene"))
                for s in (brief.get("required_scenes") or [])}
    required_scenes = {s for _, s in required}

    # 4. Hard constraints: signal present + violates -> 明確不符.
    #    Signal absent while constrained -> 證據不足 (CLEAR can land here).
    #    has_people is tri-state: True violates no_people; missing/null
    #    cannot prove absence -> Needs Review; non-boolean is a data
    #    error -> Needs Review, never passes.
    if hard.get("no_people"):
        used.append("has_people")
        hp = signals.get("has_people")
        if isinstance(hp, bool):
            if hp is True:
                return out(VERDICT_MISMATCH, BUCKET_REMAINING,
                           "明確不符：brief 要求無人物",
                           [], "constraint")
        elif hp is None:
            return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                       "證據不足：缺人物訊號，無法核對無人物約束",
                       ["補人物訊號"], "constraint")
        else:
            return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                       "資料錯誤：has_people 非 boolean（{}），不得通過".format(
                           type(hp).__name__),
                       ["修正人物訊號為 boolean"], "constraint")
    min_edge = hard.get("min_long_edge")
    if min_edge is not None:
        used.append("long_edge")
        edge = signals.get("long_edge")
        if edge is None:
            return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                       "證據不足：缺解析度訊號，無法核對最小邊",
                       ["補長邊像素數"], "constraint")
        if edge < min_edge:
            return out(VERDICT_MISMATCH, BUCKET_REMAINING,
                       "明確不符：解析度低於 brief 下限",
                       [], "constraint")
    allowed = hard.get("allowed_channels")
    if allowed:
        used.append("channel")
        channel = signals.get("channel")
        if channel is None:
            return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                       "證據不足：缺通路訊號，無法核對通路",
                       ["補通路"], "constraint")
        if channel not in allowed:
            return out(VERDICT_MISMATCH, BUCKET_REMAINING,
                       "明確不符：通路非 brief 允許",
                       [], "constraint")
    live = facts.get("live_skus")
    if live:
        used.append("sku")
        sku = signals.get("sku")
        if sku is None:
            return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                       "證據不足：缺 SKU，無法核對上架事實",
                       ["補 SKU"], "constraint")
        if sku not in live:
            return out(VERDICT_MISMATCH, BUCKET_REMAINING,
                       "明確不符：SKU 非本次上架",
                       [], "constraint")

    # 5. Scene: missing claim -> insufficient; unrequested -> mismatch.
    used.append("scene_claim")
    claim = signals.get("scene_claim")
    if not claim:
        return out(VERDICT_INSUFFICIENT, BUCKET_REVIEW,
                   "證據不足：無法判定場景槽位",
                   ["由人工指派場景"], "scene")
    if claim not in required_scenes:
        return out(VERDICT_MISMATCH, BUCKET_REMAINING,
                   "明確不符：場景非本次需求",
                   [], "scene")

    return out(VERDICT_MATCH, BUCKET_SHORTLIST,
               "符合：場景與硬約束皆通過",
               [], "scene")
