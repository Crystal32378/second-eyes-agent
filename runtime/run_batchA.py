"""Batch A blind runner — QUARANTINED until synthetic lock + quota recovery.

Single locked model, hash-gated reader, fresh outputs to outputs/.
Evaluator-only artifacts (observations.jsonl, inventory, summaries, run logs)
are NEVER imported here.

DO NOT RUN before synthetic pass. DO NOT precompute answers.
"""
BLOCKED_REASON = "Needs synthetic lock + Bedrock quota recovery"
print(f"BLOCKED: {BLOCKED_REASON}")
