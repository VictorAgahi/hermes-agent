"""
Moteur Telegram Long Polling pour Hermes Core.
Invariant 1 : Long Polling strict exclusif via getUpdates (drop_pending_updates=True).
Zero port public ouvert.
"""

import asyncio
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
import redis.asyncio as redis

from src.config import Settings
from src.bot.handlers import BotHandlers
from src.bot.security import restricted

logger = logging.getLogger("hermes.bot.engine")

class TelegramEngine:
    def __init__(self, settings: Settings, redis_client: redis.Redis):
        self.settings = settings
        self.redis = redis_client
        self.handlers = BotHandlers(settings, redis_client)
        self.app: Optional[Application] = None

    def build_application(self) -> Optional[Application]:
        if self.settings.is_mock_telegram:
            logger.info("[INFO] Telegram Bot configured in DRY-RUN / MOCK mode (token is mock or unset)")
            return None

        app = ApplicationBuilder().token(self.settings.telegram_bot_token).build()

        # Enregistrement des commandes avec controle de securite
        auth_guard = restricted(self.settings.telegram_allowed_user_id)

        app.add_handler(CommandHandler("start", auth_guard(self.handlers.start)))
        app.add_handler(CommandHandler("ping", auth_guard(self.handlers.ping)))
        app.add_handler(CommandHandler("status", auth_guard(self.handlers.status)))
        app.add_handler(CommandHandler("sync_calendar", auth_guard(self.handlers.sync_calendar)))

        # Messages texte non-commande
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auth_guard(self.handlers.default_message)))

        self.app = app
        return app

    async def start_polling(self, stop_event: asyncio.Event):
        if self.app is None:
            # Mode Simulation / Dry-run pour CI et dev sans token
            logger.info("[INFO] Mock polling loop running. Waiting for stop signal...")
            await stop_event.wait()
            logger.info("[INFO] Mock polling loop terminated cleanly")
            return

        logger.info("[INFO] Starting Telegram Bot in strict Long Polling mode (Invariant 1)...")
        # 1. Initialisation
        await self.app.initialize()
        await self.app.start()

        # 2. Demarrage du Long Polling avec drop_pending_updates=True
        if self.app.updater:
            await self.app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            logger.info("[INFO] Telegram Bot listening on getUpdates (0 open ports)")

        # 3. Attente du signal d'arret
        await stop_event.wait()

        # 4. Arret propre
        logger.info("[INFO] Shutting down Telegram Bot Long Polling...")
        if self.app.updater:
            await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("[INFO] Telegram Bot stopped cleanly")
