"""Инлайн-клавиатуры бота.

Формат callback_data:
  movies:page:<n>   — страница списка фильмов
  movie:<id>        — карточка фильма
  play:<id>         — запустить фильм
  ctl:playpause     — пауза/плей
  ctl:stop          — стоп
  ctl:volup         — громкость +
  ctl:voldown       — громкость -
  now               — что сейчас играет
"""

from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

PAGE_SIZE = 10


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню из /start."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎬 Фильмы", callback_data="movies:page:0"))
    builder.row(InlineKeyboardButton(text="▶️ Сейчас играет", callback_data="now"))
    builder.row(
        InlineKeyboardButton(text="⏯", callback_data="ctl:playpause"),
        InlineKeyboardButton(text="⏹", callback_data="ctl:stop"),
        InlineKeyboardButton(text="🔉 -", callback_data="ctl:voldown"),
        InlineKeyboardButton(text="🔊 +", callback_data="ctl:volup"),
    )
    return builder.as_markup()


def movies_list_kb(movies: list[dict[str, Any]], page: int, total: int) -> InlineKeyboardMarkup:
    """Список фильмов кнопками + пагинация ⬅️/➡️."""
    builder = InlineKeyboardBuilder()
    for movie in movies:
        year = f" ({movie['year']})" if movie.get("year") else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{movie.get('title', 'Без названия')}{year}",
                callback_data=f"movie:{movie['movieid']}",
            )
        )

    # Кнопки пагинации показываем только там, где есть куда листать
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"movies:page:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"movies:page:{page + 1}"))
    if nav:
        builder.row(*nav)
    return builder.as_markup()


def search_results_kb(movies: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """Результаты поиска — просто кнопки с фильмами."""
    builder = InlineKeyboardBuilder()
    for movie in movies:
        year = f" ({movie['year']})" if movie.get("year") else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{movie.get('title', 'Без названия')}{year}",
                callback_data=f"movie:{movie['movieid']}",
            )
        )
    return builder.as_markup()


def movie_card_kb(movie_id: int) -> InlineKeyboardMarkup:
    """Кнопки под карточкой фильма."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="▶️ Смотреть", callback_data=f"play:{movie_id}"))
    builder.row(InlineKeyboardButton(text="🎬 К списку фильмов", callback_data="movies:page:0"))
    return builder.as_markup()


def player_controls_kb() -> InlineKeyboardMarkup:
    """Пульт управления воспроизведением."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏯", callback_data="ctl:playpause"),
        InlineKeyboardButton(text="⏹", callback_data="ctl:stop"),
    )
    builder.row(
        InlineKeyboardButton(text="🔉 -", callback_data="ctl:voldown"),
        InlineKeyboardButton(text="🔊 +", callback_data="ctl:volup"),
    )
    builder.row(InlineKeyboardButton(text="ℹ️ Что играет", callback_data="now"))
    return builder.as_markup()
