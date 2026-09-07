"""Closed vocabularies — the ONLY fields on which CONFLICT can be asserted.

The model may only select tokens from these lists. The program compares
tokens; it never asks the model "do these conflict?". Anything outside
these lists is non-comparable and can NEVER produce CONFLICT — at most
UNKNOWN. Boundary we can state aloud: "we assert conflict only on
comparable fields."
"""

COLOURS = frozenset({
    "beige", "red", "black", "white", "blue", "gray", "brown", "green",
})

ITEM_TYPES = frozenset({
    "dress", "jacket", "top", "bottom", "outerwear", "bag", "shoe",
    "accessory",
})

SHOTS = frozenset({
    "flat-lay", "product-shot", "detail", "full-look", "on-hanger",
})

FIELDS = ("colour", "item", "shot")

VOCABS = {
    "colour": COLOURS,
    "item": ITEM_TYPES,
    "shot": SHOTS,
}


def normalize(field: str, token: str | None) -> str | None:
    """Return the token iff it is in-vocab, else None (non-comparable)."""
    if token is None:
        return None
    token = token.strip().lower()
    return token if token in VOCABS[field] else None
