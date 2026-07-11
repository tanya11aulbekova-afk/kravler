"""Хендлеры /start и главного меню."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_menu_kb

router = Router(name="common")

WELCOME_TEXT = (
    "Привет! Я пульт для твоего медиацентра Kodi. 🎬\n\n"
    "Что умею:\n"
    "• /movies — список фильмов из библиотеки\n"
    "• /now — что сейчас играет\n"
    "• Напиши название фильма — найду его в библиотеке\n\n"
    "Кнопки ниже — быстрый доступ:"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие + главное меню."""
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
