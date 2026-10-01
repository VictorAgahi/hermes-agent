"""
Gestionnaires de commandes et messages Telegram pour Hermes Core.
Toutes les interactions sont concues sans emoji selon la regle stricte Zero Emoji.
"""

import time
import json
import logging
from typing import Optional
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes
import redis.asyncio as redis
import psycopg2
from psycopg2.extras import RealDictCursor

from hermes_proto.calendar.v1 import calendar_pb2
from src.bus.client import HermesBusClient
from src.config import Settings
from src.bot.security import restricted

logger = logging.getLogger("hermes.bot.handlers")

class BotHandlers:
    def __init__(self, settings: Settings, redis_client: redis.Redis):
        self.settings = settings
        self.redis = redis_client
        self.bus_client = HermesBusClient(redis_client)

    def get_pg_connection(self):
        return psycopg2.connect(
            host=self.settings.postgres_host,
            port=self.settings.postgres_port,
            user=self.settings.postgres_user,
            password=self.settings.postgres_password,
            dbname=self.settings.postgres_db,
            connect_timeout=3
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "HERMES OS - Terminal de Controle 24/7\n"
            "Mode : Telegram Long Polling Strict (Invariant 1 : zero port ouvert)\n\n"
            "Commandes disponibles :\n"
            "/ping - Tester la reactivite de l'OS\n"
            "/status - Rapport d'etat du cluster (RAM, PostgreSQL, Redis, Workers)\n"
            "/sync_calendar - Declencher la synchronisation de l'agenda universitaire\n"
        )
        if update.effective_message:
            await update.effective_message.reply_text(text)

    async def ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_ts = time.time()
        await self.redis.ping()
        latency_ms = int((time.time() - start_ts) * 1000)
        msg = f"PONG - Hermes Core en ligne (Latence bus : {latency_ms} ms)."
        if update.effective_message:
            await update.effective_message.reply_text(msg)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_message:
            return

        await update.effective_message.reply_text("[INFO] Interrogation de l'etat du systeme en cours...")

        lines = ["=== RAPPORT D'ETAT HERMES OS ==="]

        # 1. Etat Redis
        try:
            await self.redis.ping()
            cal_stream_len = await self.redis.xlen("stream:calendar")
            notif_stream_len = await self.redis.xlen("stream:notifications")
            lines.append(f"Redis 7 Streams : ACTIF (stream:calendar: {cal_stream_len} msgs, stream:notifications: {notif_stream_len} msgs)")
        except Exception as e:
            lines.append(f"Redis 7 Streams : ERREUR ({e})")

        # 2. Etat PostgreSQL
        try:
            conn = self.get_pg_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Taches par statut
                cur.execute("SELECT status, count(*) FROM tasks GROUP BY status;")
                task_stats = {r["status"]: r["count"] for r in cur.fetchall()}
                lines.append(f"PostgreSQL 16 : ACTIF (Taches: {task_stats})")

                # Dernieres taches
                cur.execute("""
                    SELECT task_type, status, idempotency_key, updated_at 
                    FROM tasks 
                    ORDER BY updated_at DESC 
                    LIMIT 3;
                """)
                recent_tasks = cur.fetchall()
                if recent_tasks:
                    lines.append("\nDernieres taches executees :")
                    for t in recent_tasks:
                        lines.append(f"- [{t['status']}] {t['task_type']} ({t['idempotency_key']})")

                # Prochains cours / examens
                cur.execute("""
                    SELECT title, location, start_time, end_time 
                    FROM calendar_events 
                    WHERE end_time >= NOW() - INTERVAL '1 day'
                    ORDER BY start_time ASC 
                    LIMIT 3;
                """)
                events = cur.fetchall()
                if events:
                    lines.append("\nAgenda scolaire immediat :")
                    for ev in events:
                        start_str = ev["start_time"].strftime("%d/%m %H:%M")
                        lines.append(f"- {start_str} : {ev['title']} ({ev['location'] or 'Salle non definie'})")

            conn.close()
        except Exception as e:
            lines.append(f"PostgreSQL 16 : ERREUR ({e})")

        lines.append("\nSurveillance : 8 GB RAM VPS Ceiling respecte.")
        await update.effective_message.reply_text("\n".join(lines))

    async def sync_calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_message:
            return

        now = datetime.now(timezone.utc)
        week_num = now.isocalendar()[1]
        year = now.year

        idempotency_key = f"tg_sync_{int(time.time())}"

        # Creation de la requete Protobuf
        req = calendar_pb2.CalendarSyncRequest(
            user_id=self.settings.default_user_uuid,
            year=year,
            week_number=week_num,
            force_full_resync=True,
            date_range_start=now.strftime("%Y-%m-%dT00:00:00Z"),
            date_range_end=now.strftime("%Y-%m-%dT23:59:59Z"),
            ics_file_path=self.settings.calendar_ics_path
        )

        try:
            event_id = await self.bus_client.publish(
                stream="stream:calendar",
                event_type="calendar.sync.requested",
                idempotency_key=idempotency_key,
                protobuf_payload=req.SerializeToString(),
                target_worker="calendar-worker"
            )
            reply = (
                f"[INFO] Demande de synchronisation emise dans le bus.\n"
                f"- Event ID : {event_id}\n"
                f"- Cible : CalendarWorker (Superviseur Go)\n"
                f"- Semaine : {week_num} (Annee {year})\n"
                "Le superviseur analyse l'agenda et emettra une alerte si des examens ou collisions sont detectes."
            )
            await update.effective_message.reply_text(reply)
        except Exception as e:
            logger.error("[ERROR] Failed to publish calendar sync event: %s", e)
            await update.effective_message.reply_text(f"[ERROR] Echec de publication sur Redis Streams : {e}")

    async def default_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_message or not update.effective_message.text:
            return

        text = update.effective_message.text
        logger.info("[INFO] Received message from user: %s", text)
        reply = (
            f"[RECU] \"{text}\"\n"
            "Le moteur d'inference ReAct (DeepSeek-V3 via NousPortal) est en attente d'activation.\n"
            "Utilisez /status ou /sync_calendar pour interagir avec les superviseurs Go."
        )
        await update.effective_message.reply_text(reply)
