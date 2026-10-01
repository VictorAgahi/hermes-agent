"""
Hermes Core Orchestrator - Point d'entree unifie (Python 3.12).
Execute le Bot Telegram en Long Polling et l'ecouteur de notifications Redis Streams en parallele.
Strict Zero Emoji Policy. Invariant 1 (Zero port public) et Invariant 2 (Budget RAM < 900 Mo).
"""

import asyncio
import logging
import signal
import sys

import redis.asyncio as redis

from src.config import load_settings
from src.bot.engine import TelegramEngine
from src.bot.notifier import NotificationListener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("hermes.core")

async def main():
    logger.info("[INFO] Starting Hermes Core Orchestrator (Python 3.12)...")
    settings = load_settings()

    # 1. Connexion Redis Streams
    logger.info("[INFO] Connecting to Redis Streams (%s:%d)...", settings.redis_host, settings.redis_port)
    rdb = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        decode_responses=False
    )
    try:
        await rdb.ping()
        logger.info("[INFO] Connected to Redis 7 Streams successfully")
    except Exception as e:
        logger.error("[FATAL] Could not connect to Redis: %v", e)
        sys.exit(1)

    # 2. Preparation des composants asynchrones
    stop_event = asyncio.Event()

    # Gestion des signaux de terminaison (SIGINT, SIGTERM)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: stop_event.set())
        except NotImplementedError:
            # Pour compatibilite Windows / certains environnements
            pass

    # Moteur Telegram
    telegram_engine = TelegramEngine(settings, rdb)
    app = telegram_engine.build_application()
    bot_instance = app.bot if app else None

    # Ecouteur de notifications
    notifier = NotificationListener(settings, rdb, bot_instance)

    logger.info("[INFO] Launching Telegram Long Polling & Notification Dispatcher...")

    try:
        await asyncio.gather(
            telegram_engine.start_polling(stop_event),
            notifier.start(stop_event)
        )
    finally:
        logger.info("[INFO] Closing Redis connections...")
        await rdb.aclose()
        logger.info("[INFO] Hermes Core Orchestrator shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
