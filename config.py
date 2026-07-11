"""Загрузка настроек из .env через python-dotenv + валидация pydantic."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """Все настройки бота. Значения берутся из переменных окружения (.env)."""

    bot_token: str = Field(min_length=1)
    kodi_host: str = Field(min_length=1)
    kodi_port: int = 8080
    kodi_login: str = "kodi"
    kodi_password: str = ""
    allowed_users: list[int] = Field(min_length=1)

    @field_validator("allowed_users", mode="before")
    @classmethod
    def _parse_allowed_users(cls, value: object) -> object:
        # ALLOWED_USERS в .env — строка вида "123456,789012"
        if isinstance(value, str):
            return [int(part) for part in value.split(",") if part.strip()]
        return value


def load_settings() -> Settings:
    """Прочитать .env и вернуть провалидированные настройки.

    Падает с понятной ошибкой pydantic, если что-то не заполнено.
    """
    load_dotenv()
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        kodi_host=os.getenv("KODI_HOST", ""),
        kodi_port=int(os.getenv("KODI_PORT", "8080")),
        kodi_login=os.getenv("KODI_LOGIN", "kodi"),
        kodi_password=os.getenv("KODI_PASSWORD", ""),
        allowed_users=os.getenv("ALLOWED_USERS", ""),
    )
