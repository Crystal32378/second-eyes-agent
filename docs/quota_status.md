# QUOTA-BLOCKER STATUS (updated per check, no retries fired)

- AWS profile `muse-spark`, region `us-east-1`: CONNECTED (least-privilege).
- Nova Lite (`amazon.nova-lite-v1:0`) + Nova Pro (`amazon.nova-pro-v1:0`):
  visible, TEXT/IMAGE/VIDEO in, TEXT out, streaming supported.
- Minimal Converse call reached Bedrock but returned
  `ThrottlingException: Too many tokens per day` → connectivity PASS,
  inference PASS NOT claimed.
- Rule: no retry bombardment, no model/region bypass, no mocks as results.
- Next: re-check quota with a single minimal call only when instructed.
