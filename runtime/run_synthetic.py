"""Synthetic runner — QUARANTINED until Bedrock quota recovers.

Runs fixtures/synthetic/cases.json through the Strands agent on
Nova Lite and Nova Pro (one pass each), checks CLEAR/CONFLICT/UNKNOWN
routing + tool calls + logging, then locks prompt/tools.

DO NOT RUN while quota blocked. DO NOT mock Bedrock results.
"""
BLOCKED_REASON = "Bedrock daily token quota ThrottlingException"
print(f"BLOCKED: {BLOCKED_REASON}")
