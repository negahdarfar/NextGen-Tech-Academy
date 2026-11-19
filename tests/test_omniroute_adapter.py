import os
import unittest
from unittest.mock import patch

from nextgen_academy import llm


class OmniRouteAdapterTests(unittest.TestCase):
    @patch.dict(os.environ, {
        "OMNIROUTE_API_KEY": "test-endpoint-key",
        "OMNIROUTE_BASE_URL": "https://gateway.example.test/v1",
        "OMNIROUTE_MODEL": "auto/subscription",
    }, clear=True)
    @patch("nextgen_academy.llm._post")
    def test_uses_openai_compatible_endpoint_and_auth(self, post):
        post.return_value = {
            "choices": [{"message": {"content": "{\\"title\\": \\"ok\\"}"}}]
        }

        result = llm._omniroute("system", "user")

        self.assertEqual(result, '{"title": "ok"}')
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://gateway.example.test/v1/chat/completions")
        self.assertEqual(args[1]["model"], "auto/subscription")
        self.assertEqual(args[2]["Authorization"], "Bearer test-endpoint-key")
        self.assertEqual(kwargs["timeout"], 180)

    @patch.dict(os.environ, {
        "OMNIROUTE_API_KEY": "test-endpoint-key",
        "OMNIROUTE_BASE_URL": "http://127.0.0.1:20128/v1",
    }, clear=True)
    @patch("nextgen_academy.llm._post")
    def test_local_base_url_is_supported_for_local_runs(self, post):
        post.return_value = {"choices": [{"message": {"content": "{}"}}]}

        llm._omniroute("system", "user")

        self.assertEqual(post.call_args.args[0],
                         "http://127.0.0.1:20128/v1/chat/completions")

    @patch.dict(os.environ, {
        "OMNIROUTE_API_KEY": "test-endpoint-key",
        "OMNIROUTE_BASE_URL": "file:///tmp/gateway",
    }, clear=True)
    def test_rejects_non_http_urls(self):
        with self.assertRaises(llm.LLMError):
            llm._omniroute("system", "user")


if __name__ == "__main__":
    unittest.main()
