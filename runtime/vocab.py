"""FROZEN closed vocabularies — enumerated from Batch A 60 rel_paths, then frozen.

Freeze date: before any blind run. Rule: adding vocabulary AFTER a run is
tuning to answers and is FORBIDDEN. Any future change requires a new freeze
note + full re-run, never a quiet edit.

Per-token hit counts in the 60 paths (mechanical substring scan):
  COLOURS: beige 3, pink 1, white 0, blue 0, black 0,
           膚 3, 粉 3, 黑 2, 藍 1, 白 0
  ITEMS:   bra 4, bralette 1, balconette 1, panty 1,
           抹胸 3, 內衣 0, 褲 0, 深V 0
  SHOTS:   product 4, detail 2, close-up 2, snapshot 0, snap shot 1, 正側背 3

Zero-hit tokens (white/blue/black/白/snapshot/內衣/褲/深V) are kept as
harmless counterparts; they can never match and therefore never route.
Excluded deliberately: 蕾絲/波蕾/雪紡 (fabric or series names, not one of
the three comparable fields).

Matching semantics:
- Model side (observed): EXACT token membership + mandatory evidence_ref.
- Old/path side (free text, incl. CJK with no word boundaries):
  case-insensitive SUBSTRING scan, longest token first for specificity
  (e.g. "bralette" wins over "bra" inside "Bralette").
"""

COLOURS = ("beige", "pink", "white", "blue", "black",
           "膚", "粉", "黑", "藍", "白")

ITEM_TYPES = ("bra", "bralette", "balconette", "panty",
              "抹胸", "內衣", "褲", "深V")

SHOTS = ("product", "detail", "close-up", "snapshot", "snap shot", "正側背")

FIELDS = ("colour", "item", "shot")

VOCABS = {
    "colour": COLOURS,
    "item": ITEM_TYPES,
    "shot": SHOTS,
}


def _ordered(field: str):
    return sorted(VOCABS[field], key=len, reverse=True)


def normalize(field: str, token: str | None) -> str | None:
    """Model side: exact membership only."""
    if token is None:
        return None
    token = token.strip().lower()
    return token if token in VOCABS[field] else None


def scan_old(field: str, text: str | None) -> str | None:
    """Old/path side: substring scan over free text (CJK-safe).

    Returns the longest matching token, or None if non-comparable.
    """
    if not text:
        return None
    lowered = text.lower()
    for token in _ordered(field):
        if token.lower() in lowered:
            return token.lower()
    return None
