"""Middleware безопасности: пропускаем только пользователей из ALLOWED_USERS."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)

DENY_TEXT = (
    "Извините, это личный бот для домашнего медиацентра, "
    "доступ к нему ограничен. 🙂"
)


class AllowedUsersMiddleware(BaseMiddleware):
    """Отсекает все сообщения и колбэки от пользователей не из белого списка."""

    def __init__(self, allowed_users: list[int]) -> None:
        self._allowed = set(allowed_users)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        user_id = user.id if user else None

        if user_id in self._allowed:
            return await handler(event, data)

        # Чужой пользователь: вежливо отказываем и не передаём событие дальше
        logger.info("Отказ в доступе: user_id=%s", user_id)
        if isinstance(event, Message):
            await event.answer(DENY_TEXT)
        elif isinstance(event, CallbackQuery):
            await event.answer(DENY_TEXT, show_alert=True)
        return None
