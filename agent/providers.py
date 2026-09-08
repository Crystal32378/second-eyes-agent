"""Model providers for Second Eyes.

Provider setup is deliberately separate from routing. Models may describe
evidence; only ``agent.loop.route`` decides CLEAR/CONFLICT/UNKNOWN/NEW.
"""

from __future__ import annotations

import os

from google import genai
from strands import Agent
from strands.models.gemini import GeminiModel

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_VERTEX_LOCATION = "global"

SYSTEM_PROMPT = """You are the observation provider for Second Eyes.
Describe only evidence present in the supplied input. Never choose a routing
state and never fill missing evidence. For this connectivity check, reply with
exactly SECOND_EYES_GEMINI_OK and nothing else.
"""


def build_gemini_model() -> GeminiModel:
    """Build Gemini using an API key when present, otherwise Vertex ADC.

    No credential is read from a repository file or written to logs.
    """
    model_id = os.getenv("SECOND_EYES_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return GeminiModel(
            client_args={"api_key": api_key},
            model_id=model_id,
            params={"temperature": 0, "max_output_tokens": 256},
        )

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError(
            "Set GEMINI_API_KEY/GOOGLE_API_KEY, or set GOOGLE_CLOUD_PROJECT "
            "and authenticate with Google Cloud Application Default Credentials."
        )
    location = os.getenv("GOOGLE_CLOUD_LOCATION", DEFAULT_VERTEX_LOCATION)
    client = genai.Client(vertexai=True, project=project, location=location)
    return GeminiModel(
        client=client,
        model_id=model_id,
        params={"temperature": 0, "max_output_tokens": 256},
    )


def build_gemini_agent() -> Agent:
    """Build a tool-free provider smoke-test agent."""
    return Agent(
        model=build_gemini_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        callback_handler=None,
    )
