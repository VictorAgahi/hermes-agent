"""
Configuration centralisee pour Hermes Core Orchestrator.
Valide les variables d'environnement pour Telegram, Redis Streams et PostgreSQL.
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    # Telegram Bot
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "dev_mock_token")
    telegram_allowed_user_id: int = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0"))
    
    # Redis Streams
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "hermes_redis_dev_secret_2026")
    
    # PostgreSQL 16
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "hermes")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "hermes_dev_secret_2026")
    postgres_db: str = os.getenv("POSTGRES_DB", "hermes")

    # Invariants & Defaults
    default_user_uuid: str = "00000000-0000-0000-0000-000000000001"
    calendar_ics_path: str = os.getenv("CALENDAR_ICS_PATH", "")

    @property
    def is_mock_telegram(self) -> bool:
        return not self.telegram_bot_token or self.telegram_bot_token.startswith("dev_mock")

def load_settings() -> Settings:
    return Settings()
