"""Сборка всех роутеров в один, чтобы bot.py подключал их одной строкой."""

from aiogram import Router

from handlers.common import router as common_router
from handlers.movies import router as movies_router
from handlers.player import router as player_router


def setup_routers() -> Router:
    """Вернуть корневой роутер со всеми хендлерами.

    Порядок важен: movies_router содержит "ловец текста" для поиска,
    поэтому подключается последним.
    """
    root = Router(name="root")
    root.include_router(common_router)
    root.include_router(player_router)
    root.include_router(movies_router)
    return root
