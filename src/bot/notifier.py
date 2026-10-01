"""
Ecouteur asynchrone des flux de notifications Redis Streams (stream:notifications).
Pousse automatiquement les alertes critiques des workers (examens, collisions, HITL) vers Telegram.
"""

import asyncio
import json
import logging
from typing import Optional

from telegram import Bot
import redis.asyncio as redis

from src.config import Settings

logger = logging.getLogger("hermes.bot.notifier")

class NotificationListener:
    def __init__(self, settings: Settings, redis_client: redis.Redis, bot: Optional[Bot]):
        self.settings = settings
        self.redis = redis_client
        self.bot = bot
        self.stream = "stream:notifications"
        self.group = "cg:notif:core"
        self.consumer = "hermes-core-notifier"

    async def start(self, stop_event: asyncio.Event):
        # 1. S'assurer de l'existence du consumer group
        try:
            await self.redis.xgroup_create(self.stream, self.group, id="0", mkstream=True)
            logger.info("[INFO] Consumer group '%s' created on stream '%s'", self.group, self.stream)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.warning("[WARN] Could not ensure consumer group for notifications: %s", e)

        logger.info("[INFO] Notification listener active on '%s'", self.stream)

        # 2. Boucle de consommation
        while not stop_event.is_set():
            try:
                entries = await self.redis.xreadgroup(
                    groupname=self.group,
                    consumername=self.consumer,
                    streams={self.stream: ">"},
                    count=5,
                    block=2000
                )

                if not entries:
                    continue

                for stream_name, messages in entries:
                    for msg_id, values in messages:
                        await self.process_notification(msg_id, values)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("[WARN] Notification loop exception: %s", e)
                await asyncio.sleep(1.0)

        logger.info("[INFO] Notification listener stopped cleanly")

    async def process_notification(self, msg_id: bytes, values: dict):
        msg_id_str = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
        try:
            meta_raw = values.get(b"meta") or values.get("meta")
            if not meta_raw:
                await self.redis.xack(self.stream, self.group, msg_id_str)
                return

            meta = json.loads(meta_raw)
            title = meta.get("title", "Alerte Hermes")
            message = meta.get("message", "")
            target_chat_id = meta.get("chat_id") or self.settings.telegram_allowed_user_id

            logger.info("[INFO] Received notification event: '%s' for chat_id %s", title, target_chat_id)

            if self.bot and target_chat_id and target_chat_id > 0:
                formatted_text = f"[ALERTE] {title}\n\n{message}"
                try:
                    await self.bot.send_message(chat_id=target_chat_id, text=formatted_text)
                    logger.info("[INFO] Dispatched Telegram notification to %s", target_chat_id)
                except Exception as send_err:
                    logger.error("[ERROR] Failed to send Telegram notification: %s", send_err)

            # Acquittement garanti
            await self.redis.xack(self.stream, self.group, msg_id_str)
        except Exception as err:
            logger.error("[ERROR] Failed to process notification %s: %s", msg_id_str, err)
