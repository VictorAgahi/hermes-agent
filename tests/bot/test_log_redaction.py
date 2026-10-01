"""
Tests du masquage des secrets dans les logs (token du bot Telegram).
Strict Zero Emoji Policy.
"""

import io
import logging
import unittest

from src.log_redaction import REDACTED, RedactingFormatter, configure_logging, redact

# Shape of a real token, not a real one
FAKE_TOKEN = "1234567890:AAFSyy-bR30ZtpXD9B_Yc6vmtqygM1MmFAB"


class TestLogRedaction(unittest.TestCase):
    def setUp(self):
        self.stream = io.StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(RedactingFormatter("%(name)s %(message)s"))
        self.logger = logging.getLogger("test.redaction")
        self.logger.handlers = [handler]
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)

    def test_token_in_httpx_style_url_is_masked(self):
        self.logger.info(
            'HTTP Request: POST %s "HTTP/1.1 200 OK"',
            f"https://api.telegram.org/bot{FAKE_TOKEN}/getUpdates",
        )
        out = self.stream.getvalue()
        self.assertNotIn(FAKE_TOKEN, out)
        self.assertIn(f"/bot{REDACTED}/getUpdates", out)

    def test_token_in_exception_traceback_is_masked(self):
        try:
            raise RuntimeError(f"connection failed for https://api.telegram.org/bot{FAKE_TOKEN}/sendMessage")
        except RuntimeError:
            self.logger.exception("[ERROR] send failed")
        self.assertNotIn(FAKE_TOKEN, self.stream.getvalue())

    def test_unrelated_text_is_untouched(self):
        text = "Received notification event: 'Verification expiree' for chat_id 5986257342 at 08:15:28"
        self.assertEqual(redact(text), text)

    def test_httpx_info_logs_are_silenced(self):
        configure_logging(logging.INFO)
        try:
            self.assertFalse(logging.getLogger("httpx").isEnabledFor(logging.INFO))
            self.assertTrue(logging.getLogger("httpx").isEnabledFor(logging.WARNING))
            self.assertTrue(logging.getLogger("hermes.core").isEnabledFor(logging.INFO))
        finally:
            logging.getLogger("httpx").setLevel(logging.NOTSET)
            logging.getLogger("httpcore").setLevel(logging.NOTSET)


if __name__ == "__main__":
    unittest.main()
