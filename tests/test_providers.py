import os
import unittest
from unittest.mock import Mock, patch

from agent.providers import build_gemini_model


class GeminiProviderTests(unittest.TestCase):
    @patch("agent.providers.GeminiModel")
    def test_api_key_path(self, model):
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only", "SECOND_EYES_GEMINI_MODEL": "gemini-test"},
            clear=True,
        ):
            build_gemini_model()
        model.assert_called_once_with(
            client_args={"api_key": "test-only"},
            model_id="gemini-test",
            params={"temperature": 0, "max_output_tokens": 256},
        )

    @patch("agent.providers.GeminiModel")
    @patch("agent.providers.genai.Client")
    def test_vertex_adc_path(self, client, model):
        fake_client = Mock()
        client.return_value = fake_client
        with patch.dict(
            os.environ,
            {"GOOGLE_CLOUD_PROJECT": "test-project", "GOOGLE_CLOUD_LOCATION": "global"},
            clear=True,
        ):
            build_gemini_model()
        client.assert_called_once_with(vertexai=True, project="test-project", location="global")
        model.assert_called_once_with(
            client=fake_client,
            model_id="gemini-2.5-flash",
            params={"temperature": 0, "max_output_tokens": 256},
        )

    def test_credentials_are_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GOOGLE_CLOUD_PROJECT"):
                build_gemini_model()


if __name__ == "__main__":
    unittest.main()
