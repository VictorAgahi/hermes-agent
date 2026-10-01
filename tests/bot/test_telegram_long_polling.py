"""
Tests unitaires pour Hermes Telegram Engine & Handlers (Python 3.12 unittest).
Strict Zero Emoji Policy. Invariant 1 (Zero port public) et Invariant 2 (Budget RAM).
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock

from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from src.config import Settings
from src.bot.security import restricted
from src.bot.handlers import BotHandlers
from src.bot.notifier import NotificationListener
from hermes_proto.calendar.v1 import calendar_pb2


class TestTelegramBotSuite(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings = Settings(
            telegram_bot_token="test_mock_token_12345",
            telegram_allowed_user_id=123456789,
            postgres_host="postgres",
            postgres_port=5432,
            postgres_user="hermes",
            postgres_password="hermes_dev_secret_2026",
            postgres_db="hermes",
            redis_host="redis",
            redis_port=6379,
            redis_password="hermes_redis_dev_secret_2026"
        )

        self.update = MagicMock(spec=Update)
        user = MagicMock(spec=User)
        user.id = 123456789
        user.username = "test_user"

        chat = MagicMock(spec=Chat)
        chat.id = 123456789

        message = MagicMock(spec=Message)
        message.reply_text = AsyncMock()

        self.update.effective_user = user
        self.update.effective_chat = chat
        self.update.effective_message = message

    async def test_security_decorator_allowed(self):
        called = False

        @restricted(allowed_user_id=self.settings.telegram_allowed_user_id)
        async def sample_handler(update, context):
            nonlocal called
            called = True
            return "ok"

        res = await sample_handler(self.update, MagicMock(spec=ContextTypes.DEFAULT_TYPE))
        self.assertTrue(called)
        self.assertEqual(res, "ok")

    async def test_security_decorator_rejected(self):
        self.update.effective_user.id = 999999999
        called = False

        @restricted(allowed_user_id=self.settings.telegram_allowed_user_id)
        async def sample_handler(update, context):
            nonlocal called
            called = True

        await sample_handler(self.update, MagicMock(spec=ContextTypes.DEFAULT_TYPE))
        self.assertFalse(called)
        self.update.effective_message.reply_text.assert_called_once()
        self.assertIn("Acces refuse", self.update.effective_message.reply_text.call_args[0][0])

    async def test_handler_ping(self):
        mock_redis = AsyncMock()
        handlers = BotHandlers(self.settings, mock_redis)

        await handlers.ping(self.update, MagicMock(spec=ContextTypes.DEFAULT_TYPE))
        self.update.effective_message.reply_text.assert_called_once()
        reply = self.update.effective_message.reply_text.call_args[0][0]
        self.assertIn("PONG", reply)
        self.assertIn("Hermes Core", reply)

    async def test_handler_sync_calendar(self):
        mock_redis = AsyncMock()
        mock_redis.xadd.return_value = "1790000000000-0"

        handlers = BotHandlers(self.settings, mock_redis)

        await handlers.sync_calendar(self.update, MagicMock(spec=ContextTypes.DEFAULT_TYPE))
        self.assertTrue(mock_redis.xadd.called)
        self.update.effective_message.reply_text.assert_called_once()
        reply = self.update.effective_message.reply_text.call_args[0][0]
        self.assertIn("[INFO] Demande de synchronisation emise dans le bus.", reply)
        self.assertIn("CalendarWorker (Superviseur Go)", reply)

    async def test_notifier_dispatch(self):
        mock_redis = AsyncMock()
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()

        notifier = NotificationListener(self.settings, mock_redis, mock_bot)

        payload = json.dumps({
            "title": "Examen Detecte",
            "message": "Examen de Reseau demain a 08h30 en Amphi A",
            "chat_id": 123456789
        })

        await notifier.process_notification(b"1790000000000-1", {"meta": payload})

        mock_bot.send_message.assert_called_once_with(
            chat_id=123456789,
            text="[ALERTE] Examen Detecte\n\nExamen de Reseau demain a 08h30 en Amphi A"
        )
        mock_redis.xack.assert_called_once_with("stream:notifications", "cg:notif:core", "1790000000000-1")


if __name__ == "__main__":
    unittest.main()
