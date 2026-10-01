"""
Tests d'integration live pour Hermes Telegram Engine contre PostgreSQL et Redis Streams reels.
Strict Zero Emoji Policy. Invariant 1 (Zero port public) et Invariant 2 (Budget RAM).
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock

import redis.asyncio as redis
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from src.config import load_settings
from src.bot.handlers import BotHandlers


class TestTelegramLiveIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.settings = load_settings()
        self.redis = redis.Redis(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            password=self.settings.redis_password,
            decode_responses=False
        )
        await self.redis.ping()

        self.update = MagicMock(spec=Update)
        user = MagicMock(spec=User)
        user.id = self.settings.telegram_allowed_user_id
        user.username = "live_test_user"

        chat = MagicMock(spec=Chat)
        chat.id = self.settings.telegram_allowed_user_id

        message = MagicMock(spec=Message)
        message.reply_text = AsyncMock()

        self.update.effective_user = user
        self.update.effective_chat = chat
        self.update.effective_message = message

        self.handlers = BotHandlers(self.settings, self.redis)

    async def asyncTearDown(self):
        await self.redis.aclose()

    async def test_live_ping(self):
        await self.handlers.ping(self.update, MagicMock(spec=ContextTypes.DEFAULT_TYPE))
        self.update.effective_message.reply_text.assert_called_once()
        reply = self.update.effective_message.reply_text.call_args[0][0]
        self.assertIn("PONG", reply)
        self.assertIn("Hermes Core en ligne", reply)

    async def test_live_status(self):
        await self.handlers.status(self.update, MagicMock(spec=ContextTypes.DEFAULT_TYPE))
        # Status sends 2 replies: interrogation info, then final report
        self.assertGreaterEqual(self.update.effective_message.reply_text.call_count, 2)
        report = self.update.effective_message.reply_text.call_args_list[1][0][0]
        self.assertIn("RAPPORT D'ETAT HERMES OS", report)
        self.assertIn("Redis 7 Streams : ACTIF", report)
        self.assertIn("PostgreSQL 16 : ACTIF", report)
        self.assertIn("8 GB RAM VPS Ceiling respecte", report)

    async def test_live_sync_calendar_dispatch(self):
        initial_len = await self.redis.xlen("stream:calendar")

        await self.handlers.sync_calendar(self.update, MagicMock(spec=ContextTypes.DEFAULT_TYPE))
        self.update.effective_message.reply_text.assert_called_once()
        reply = self.update.effective_message.reply_text.call_args[0][0]
        self.assertIn("Demande de synchronisation emise dans le bus", reply)
        self.assertIn("CalendarWorker (Superviseur Go)", reply)

        new_len = await self.redis.xlen("stream:calendar")
        self.assertGreater(new_len, initial_len)


if __name__ == "__main__":
    unittest.main()
