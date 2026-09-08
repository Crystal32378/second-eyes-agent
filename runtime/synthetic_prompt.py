"""LOCKED synthetic observation prompt — frozen before the Gemini run.

The token lists are generated FROM runtime/vocab.py at import time, so the
prompt can never drift from the frozen vocabulary. Do NOT edit by hand to
fit results; any change requires a new run from scratch.

Model contract: pick EXACTLY one token per field, or NONE. Strict JSON
output. The model NEVER routes — runtime route() decides afterwards.
"""

from runtime.vocab import COLOURS, ITEM_TYPES, SHOTS

PROMPT_VERSION = "syn-obs-v1"


def build_prompt() -> str:
    lines = [
        "You are the observation provider for Second Eyes.",
        "Look at the supplied image or video. For each field, reply with",
        "EXACTLY one token from its list, or NONE if not clearly observable.",
        "Output STRICT JSON only, no other text:",
        '{"colour": <token|NONE>, "item": <token|NONE>, "shot": <token|NONE>}',
        "",
        "Rules:",
        "- Describe only evidence actually visible. Never guess, never fill gaps.",
        "- NEVER choose a routing state. NEVER explain. JSON only.",
        "",
        "colour: " + ", ".join(COLOURS),
        "item: " + ", ".join(ITEM_TYPES),
        "shot: " + ", ".join(SHOTS),
    ]
    return "\n".join(lines)


OBSERVE_PROMPT = build_prompt()
