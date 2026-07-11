"""Точка входа: python bot.py"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import load_settings
from handlers import setup_routers
from kodi_client import KodiClient
from middlewares import AllowedUsersMiddleware

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = load_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Безопасность: белый список user_id проверяется до любых хендлеров
    dp.message.middleware(AllowedUsersMiddleware(settings.allowed_users))
    dp.callback_query.middleware(AllowedUsersMiddleware(settings.allowed_users))

    # Один клиент Kodi на всё приложение; прокидывается в хендлеры через DI aiogram
    kodi = KodiClient(
        host=settings.kodi_host,
        port=settings.kodi_port,
        login=settings.kodi_login,
        password=settings.kodi_password,
    )

    dp.include_router(setup_routers())

    logger.info("Бот запущен, Kodi: %s:%s", settings.kodi_host, settings.kodi_port)
    try:
        await dp.start_polling(bot, kodi=kodi)
    finally:
        await kodi.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
