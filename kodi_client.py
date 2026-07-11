"""Асинхронная обёртка над JSON-RPC API медиацентра Kodi.

Kodi принимает запросы по адресу http://<host>:<port>/jsonrpc в формате
JSON-RPC 2.0: {"jsonrpc": "2.0", "method": "...", "params": {...}, "id": 1}.
Аутентификация — HTTP Basic Auth (логин/пароль из настроек Kodi).
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import aiohttp

logger = logging.getLogger(__name__)


class KodiError(Exception):
    """Базовая ошибка при работе с Kodi."""


class KodiConnectionError(KodiError):
    """Kodi недоступен: нет сети, неверный адрес или Kodi выключен."""


class KodiApiError(KodiError):
    """Kodi ответил, но вернул ошибку JSON-RPC (например, неверный метод)."""


class KodiClient:
    """Клиент JSON-RPC API Kodi.

    Используемые методы API:
      - VideoLibrary.GetMovies       — список фильмов библиотеки
      - VideoLibrary.GetMovieDetails — карточка фильма по movieid
      - Player.Open                  — запустить воспроизведение
      - Player.GetActivePlayers      — какие плееры сейчас активны
      - Player.PlayPause             — переключить пауза/плей
      - Player.Stop                  — остановить воспроизведение
      - Player.GetItem               — что сейчас играет
      - Player.GetProperties         — позиция/длительность/процент
      - Application.SetVolume        — громкость (increment/decrement)
    """

    def __init__(self, host: str, port: int, login: str, password: str, timeout: float = 10.0) -> None:
        self._base_url = f"http://{host}:{port}"
        self._rpc_url = f"{self._base_url}/jsonrpc"
        self._auth = aiohttp.BasicAuth(login, password)
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        # Ленивое создание сессии: aiohttp требует создавать её внутри event loop
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        """Закрыть HTTP-сессию (вызывается при остановке бота)."""
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Выполнить один JSON-RPC вызов и вернуть поле result."""
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": 1}
        if params is not None:
            payload["params"] = params

        session = await self._get_session()
        try:
            async with session.post(self._rpc_url, json=payload) as resp:
                if resp.status == 401:
                    raise KodiApiError("Kodi отклонил логин/пароль (HTTP 401)")
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json()
        except aiohttp.ClientError as exc:
            logger.warning("Kodi недоступен (%s): %s", method, exc)
            raise KodiConnectionError(f"Не удалось соединиться с Kodi: {exc}") from exc
        except TimeoutError as exc:
            logger.warning("Таймаут запроса к Kodi (%s)", method)
            raise KodiConnectionError("Kodi не ответил вовремя") from exc

        if "error" in data:
            logger.error("Ошибка JSON-RPC %s: %s", method, data["error"])
            raise KodiApiError(f"Kodi вернул ошибку: {data['error'].get('message', data['error'])}")
        return data.get("result")

    # ------------------------------------------------------------------
    # Библиотека фильмов
    # ------------------------------------------------------------------

    async def get_movies(self, start: int = 0, end: int = 10) -> tuple[list[dict[str, Any]], int]:
        """Страница списка фильмов.

        Возвращает (список фильмов, общее число фильмов в библиотеке).
        limits.start/end — встроенная пагинация Kodi.
        """
        result = await self._call(
            "VideoLibrary.GetMovies",
            {
                "properties": ["title", "year"],
                "limits": {"start": start, "end": end},
                "sort": {"method": "title", "order": "ascending"},
            },
        )
        movies = result.get("movies", []) if result else []
        total = result.get("limits", {}).get("total", len(movies)) if result else 0
        return movies, total

    async def search_movies(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Поиск фильмов по подстроке в названии.

        Фильтрация выполняется на стороне Kodi через параметр filter.
        """
        result = await self._call(
            "VideoLibrary.GetMovies",
            {
                "properties": ["title", "year"],
                "filter": {"field": "title", "operator": "contains", "value": query},
                "limits": {"start": 0, "end": limit},
                "sort": {"method": "title", "order": "ascending"},
            },
        )
        return result.get("movies", []) if result else []

    async def get_movie_details(self, movie_id: int) -> dict[str, Any]:
        """Карточка фильма: название, год, рейтинг, жанры, описание, постер."""
        result = await self._call(
            "VideoLibrary.GetMovieDetails",
            {
                "movieid": movie_id,
                "properties": ["title", "year", "rating", "genre", "plot", "art", "runtime"],
            },
        )
        return result.get("moviedetails", {}) if result else {}

    async def get_poster_bytes(self, art_path: str) -> bytes | None:
        """Скачать постер из Kodi.

        Kodi отдаёт картинки по адресу /image/<url-encoded путь из поля art>.
        Telegram не может сам достучаться до домашней сети, поэтому
        скачиваем байты и отправляем их как файл.
        """
        url = f"{self._base_url}/image/{quote(art_path, safe='')}"
        session = await self._get_session()
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                return await resp.read()
        except (aiohttp.ClientError, TimeoutError):
            # Постер — не критичная часть: молча вернём None, карточка уйдёт текстом
            logger.debug("Не удалось скачать постер: %s", art_path)
            return None

    # ------------------------------------------------------------------
    # Управление воспроизведением
    # ------------------------------------------------------------------

    async def play_movie(self, movie_id: int) -> None:
        """Запустить фильм: Player.Open с item={"movieid": id}."""
        await self._call("Player.Open", {"item": {"movieid": movie_id}})

    async def _get_active_player_id(self) -> int | None:
        """ID активного плеера (нужен всем Player.* методам)."""
        players = await self._call("Player.GetActivePlayers")
        if not players:
            return None
        return int(players[0]["playerid"])

    async def pause(self) -> bool:
        """Переключить пауза/плей. Возвращает False, если ничего не играет."""
        player_id = await self._get_active_player_id()
        if player_id is None:
            return False
        await self._call("Player.PlayPause", {"playerid": player_id})
        return True

    async def stop(self) -> bool:
        """Остановить воспроизведение. Возвращает False, если ничего не играет."""
        player_id = await self._get_active_player_id()
        if player_id is None:
            return False
        await self._call("Player.Stop", {"playerid": player_id})
        return True

    async def set_volume(self, direction: str) -> int:
        """Громкость +/-: Application.SetVolume("increment"|"decrement").

        Возвращает новое значение громкости (0–100).
        """
        if direction not in ("increment", "decrement"):
            raise ValueError("direction должен быть 'increment' или 'decrement'")
        result = await self._call("Application.SetVolume", {"volume": direction})
        return int(result) if result is not None else 0

    async def get_now_playing(self) -> dict[str, Any] | None:
        """Что сейчас играет: элемент + позиция/длительность/процент.

        Возвращает None, если ничего не воспроизводится, иначе словарь:
        {"item": {...}, "time": {...}, "totaltime": {...}, "percentage": float, "speed": int}
        """
        player_id = await self._get_active_player_id()
        if player_id is None:
            return None

        item_result = await self._call(
            "Player.GetItem",
            {"playerid": player_id, "properties": ["title", "year"]},
        )
        props = await self._call(
            "Player.GetProperties",
            {"playerid": player_id, "properties": ["time", "totaltime", "percentage", "speed"]},
        )
        return {
            "item": item_result.get("item", {}) if item_result else {},
            "time": props.get("time", {}),
            "totaltime": props.get("totaltime", {}),
            "percentage": float(props.get("percentage", 0.0)),
            "speed": int(props.get("speed", 0)),
        }
