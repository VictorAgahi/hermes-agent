"""
Configuration du logging avec masquage des secrets.
Les bibliotheques HTTP (httpx, httpcore) loguent l'URL complete de chaque requete ; pour l'API
Telegram, cette URL contient le token du bot (https://api.telegram.org/bot<token>/getUpdates).
Strict Zero Emoji Policy.
"""

import logging
import re
import sys

# Telegram bot token: <bot id>:<35-char secret>. Matched anywhere, including inside URLs and tracebacks.
# No leading \b: in ".../bot123456:AA..." the id directly follows "bot", with no word boundary.
TELEGRAM_TOKEN_RE = re.compile(r"(?<!\d)\d{6,12}:[A-Za-z0-9_-]{30,}")
REDACTED = "<telegram-token-redacted>"

# Loggers that echo request URLs at INFO level on every call (long polling = every few seconds)
NOISY_HTTP_LOGGERS = ("httpx", "httpcore")


def redact(text: str) -> str:
    return TELEGRAM_TOKEN_RE.sub(REDACTED, text)


class RedactingFormatter(logging.Formatter):
    """Formats the full record (message, exception and stack) then masks secrets in the result."""

    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logging.basicConfig(level=level, handlers=[handler], force=True)

    # Successful polling requests are not worth logging; failures still surface as warnings.
    for name in NOISY_HTTP_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
