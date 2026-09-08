#!/usr/bin/env python3
"""Construct, and optionally invoke, the Second Eyes Gemini provider.

This is a connectivity check only. It does not run synthetic fixtures, touch
Batch A, lock prompts/tools, or produce Nova evidence.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR in sys.path:
    sys.path.remove(SCRIPT_DIR)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.providers import DEFAULT_GEMINI_MODEL, build_gemini_agent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoke", action="store_true", help="make one live text call")
    args = parser.parse_args()

    agent = build_gemini_agent()
    if not args.invoke:
        print(f"READY: Strands + {DEFAULT_GEMINI_MODEL} provider constructed")
        return 0

    result = agent("Connectivity check. Follow the system instruction.")
    response = str(result).strip()
    if response != "SECOND_EYES_GEMINI_OK":
        print(f"UNEXPECTED_RESPONSE: {response}")
        return 1
    print("LIVE_OK: Strands -> Gemini returned expected sentinel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
