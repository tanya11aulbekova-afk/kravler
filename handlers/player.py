"""Хендлеры управления воспроизведением и команды /now."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards import player_controls_kb
from kodi_client import KodiClient, KodiError

logger = logging.getLogger(__name__)
router = Router(name="player")

KODI_UNAVAILABLE_TEXT = (
    "😕 Не могу связаться с Kodi. Проверь, что медиацентр включён "
    "и HTTP-доступ в настройках активен."
)
NOTHING_PLAYING_TEXT = "Сейчас ничего не воспроизводится. 💤"


def _format_time(t: dict[str, int]) -> str:
    """{"hours": 1, "minutes": 23, "seconds": 45} -> "1:23:45"."""
    hours = t.get("hours", 0)
    minutes = t.get("minutes", 0)
    seconds = t.get("seconds", 0)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _progress_bar(percentage: float, width: int = 10) -> str:
    """Текстовый прогресс-бар: ▓▓▓▓░░░░░░."""
    filled = round(width * percentage / 100)
    return "▓" * filled + "░" * (width - filled)


@router.message(Command("now"))
async def cmd_now(message: Message, kodi: KodiClient) -> None:
    """Что сейчас играет: название, позиция, длительность, процент."""
    try:
        now = await kodi.get_now_playing()
    except KodiError:
        await message.answer(KODI_UNAVAILABLE_TEXT)
        return

    if now is None:
        await message.answer(NOTHING_PLAYING_TEXT)
        return

    item = now["item"]
    title = item.get("title") or item.get("label") or "Без названия"
    year = f" ({item['year']})" if item.get("year") else ""
    state = "▶️ Играет" if now["speed"] != 0 else "⏸ На паузе"
    text = (
        f"{state}: <b>{title}</b>{year}\n"
        f"{_progress_bar(now['percentage'])} {now['percentage']:.0f}%\n"
        f"⏱ {_format_time(now['time'])} / {_format_time(now['totaltime'])}"
    )
    await message.answer(text, reply_markup=player_controls_kb())


@router.callback_query(F.data == "now")
async def cb_now(callback: CallbackQuery, kodi: KodiClient) -> None:
    """Кнопка «Что играет» — то же, что /now."""
    try:
        now = await kodi.get_now_playing()
    except KodiError:
        await callback.answer(KODI_UNAVAILABLE_TEXT, show_alert=True)
        return

    if now is None:
        await callback.answer(NOTHING_PLAYING_TEXT, show_alert=True)
        return

    item = now["item"]
    title = item.get("title") or item.get("label") or "Без названия"
    year = f" ({item['year']})" if item.get("year") else ""
    state = "▶️ Играет" if now["speed"] != 0 else "⏸ На паузе"
    text = (
        f"{state}: <b>{title}</b>{year}\n"
        f"{_progress_bar(now['percentage'])} {now['percentage']:.0f}%\n"
        f"⏱ {_format_time(now['time'])} / {_format_time(now['totaltime'])}"
    )
    if callback.message:
        await callback.message.answer(text, reply_markup=player_controls_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("ctl:"))
async def cb_player_control(callback: CallbackQuery, kodi: KodiClient) -> None:
    """Кнопки пульта: пауза/плей, стоп, громкость."""
    action = callback.data.split(":", 1)[1]
    try:
        if action == "playpause":
            ok = await kodi.pause()
            await callback.answer("⏯ Ок" if ok else NOTHING_PLAYING_TEXT)
        elif action == "stop":
            ok = await kodi.stop()
            await callback.answer("⏹ Остановлено" if ok else NOTHING_PLAYING_TEXT)
        elif action == "volup":
            volume = await kodi.set_volume("increment")
            await callback.answer(f"🔊 Громкость: {volume}")
        elif action == "voldown":
            volume = await kodi.set_volume("decrement")
            await callback.answer(f"🔉 Громкость: {volume}")
        else:
            await callback.answer("Неизвестная команда")
    except KodiError:
        await callback.answer(KODI_UNAVAILABLE_TEXT, show_alert=True)
