"""Хендлеры библиотеки фильмов: список, поиск, карточка, запуск."""

from __future__ import annotations

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from keyboards import PAGE_SIZE, movie_card_kb, movies_list_kb, player_controls_kb, search_results_kb
from kodi_client import KodiClient, KodiError

logger = logging.getLogger(__name__)
router = Router(name="movies")

KODI_UNAVAILABLE_TEXT = (
    "😕 Не могу связаться с Kodi. Проверь, что медиацентр включён "
    "и HTTP-доступ в настройках активен."
)


def _movies_page_text(page: int, total: int) -> str:
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    return f"🎬 Фильмы в библиотеке ({total} шт.), страница {page + 1}/{total_pages}:"


@router.message(Command("movies"))
async def cmd_movies(message: Message, kodi: KodiClient) -> None:
    """Первая страница списка фильмов."""
    try:
        movies, total = await kodi.get_movies(start=0, end=PAGE_SIZE)
    except KodiError:
        await message.answer(KODI_UNAVAILABLE_TEXT)
        return

    if not movies:
        await message.answer("Библиотека фильмов пуста. 🤷")
        return
    await message.answer(_movies_page_text(0, total), reply_markup=movies_list_kb(movies, 0, total))


@router.callback_query(F.data.startswith("movies:page:"))
async def cb_movies_page(callback: CallbackQuery, kodi: KodiClient) -> None:
    """Пагинация списка: кнопки ⬅️/➡️."""
    page = int(callback.data.rsplit(":", 1)[1])
    try:
        movies, total = await kodi.get_movies(start=page * PAGE_SIZE, end=(page + 1) * PAGE_SIZE)
    except KodiError:
        await callback.answer(KODI_UNAVAILABLE_TEXT, show_alert=True)
        return

    # Карточка фильма — фото, его нельзя отредактировать в текст:
    # в этом случае просто отправляем список новым сообщением
    if callback.message and callback.message.text is not None:
        await callback.message.edit_text(
            _movies_page_text(page, total),
            reply_markup=movies_list_kb(movies, page, total),
        )
    elif callback.message:
        await callback.message.answer(
            _movies_page_text(page, total),
            reply_markup=movies_list_kb(movies, page, total),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("movie:"))
async def cb_movie_card(callback: CallbackQuery, kodi: KodiClient) -> None:
    """Карточка фильма: постер, название, год, рейтинг, жанр, описание."""
    movie_id = int(callback.data.split(":", 1)[1])
    try:
        details = await kodi.get_movie_details(movie_id)
    except KodiError:
        await callback.answer(KODI_UNAVAILABLE_TEXT, show_alert=True)
        return

    if not details:
        await callback.answer("Фильм не найден в библиотеке.", show_alert=True)
        return

    title = html.escape(details.get("title", "Без названия"))
    year = details.get("year")
    rating = details.get("rating")
    genres = ", ".join(details.get("genre", []))
    plot = html.escape(details.get("plot", ""))
    if len(plot) > 600:  # подпись к фото в Telegram ограничена 1024 символами
        plot = plot[:600].rsplit(" ", 1)[0] + "…"

    lines = [f"<b>{title}</b>"]
    if year:
        lines.append(f"📅 Год: {year}")
    if rating:
        lines.append(f"⭐️ Рейтинг: {rating:.1f}")
    if genres:
        lines.append(f"🎭 Жанр: {html.escape(genres)}")
    if plot:
        lines.append(f"\n{plot}")
    caption = "\n".join(lines)

    # Пытаемся приложить постер; если его нет или не скачался — карточка текстом
    poster_bytes: bytes | None = None
    poster_path = (details.get("art") or {}).get("poster")
    if poster_path:
        poster_bytes = await kodi.get_poster_bytes(poster_path)

    if callback.message:
        if poster_bytes:
            await callback.message.answer_photo(
                BufferedInputFile(poster_bytes, filename="poster.jpg"),
                caption=caption,
                reply_markup=movie_card_kb(movie_id),
            )
        else:
            await callback.message.answer(caption, reply_markup=movie_card_kb(movie_id))
    await callback.answer()


@router.callback_query(F.data.startswith("play:"))
async def cb_play_movie(callback: CallbackQuery, kodi: KodiClient) -> None:
    """Кнопка «▶️ Смотреть» — запускаем фильм и показываем пульт."""
    movie_id = int(callback.data.split(":", 1)[1])
    try:
        await kodi.play_movie(movie_id)
    except KodiError:
        await callback.answer(KODI_UNAVAILABLE_TEXT, show_alert=True)
        return

    if callback.message:
        await callback.message.answer(
            "▶️ Запускаю воспроизведение! Пульт ниже:",
            reply_markup=player_controls_kb(),
        )
    await callback.answer("Поехали! 🍿")


@router.message(F.text & ~F.text.startswith("/"))
async def search_movies(message: Message, kodi: KodiClient) -> None:
    """Поиск: любой текст без "/" считаем названием фильма."""
    query = (message.text or "").strip()
    if not query:
        return

    try:
        movies = await kodi.search_movies(query)
    except KodiError:
        await message.answer(KODI_UNAVAILABLE_TEXT)
        return

    if not movies:
        await message.answer(f"По запросу «{query}» ничего не нашлось. 🔍")
        return
    await message.answer(
        f"🔍 Нашёл по запросу «{query}»:",
        reply_markup=search_results_kb(movies),
    )
