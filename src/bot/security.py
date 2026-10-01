"""
Controle d'acces et securite pour le bot Telegram Hermes Core.
Garantit que seul l'utilisateur autorise peut interagir avec l'OS personnel.
"""

import functools
import logging
from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger("hermes.bot.security")

def restricted(allowed_user_id: int):
    """
    Decorateur limitant l'execution des commandes au seul proprietaire du bot (Victor).
    Si allowed_user_id == 0, l'acces est ouvert en mode developpement.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any):
            user = update.effective_user
            if not user:
                return

            if allowed_user_id > 0 and user.id != allowed_user_id:
                logger.warning(
                    "[WARN] Unauthorized access attempt blocked from user_id=%s username='%s'",
                    user.id,
                    user.username or "unknown",
                )
                if update.effective_message:
                    await update.effective_message.reply_text("Acces refuse. Ce terminal Hermes est strictement prive.")
                return

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
