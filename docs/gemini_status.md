# Gemini provider status

Second Eyes now has a narrow Strands + Gemini provider adapter. It is a
quota-independent execution route, not a substitute claim for Amazon Nova.

## Authentication

Use one of these credential paths; never commit keys:

1. `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
2. Vertex AI Application Default Credentials with `GOOGLE_CLOUD_PROJECT` and
   optional `GOOGLE_CLOUD_LOCATION` (default: `global`).

Default model: `gemini-2.5-flash`. Override with
`SECOND_EYES_GEMINI_MODEL`.

## Checks

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT .venv/bin/python runtime/check_gemini.py
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT .venv/bin/python runtime/check_gemini.py --invoke
```

The live check is text-only and tool-free. It does not run synthetic fixtures,
touch Batch A, lock prompts/tools, or create Nova evidence.
