# Kodi Remote Bot 🎬

Telegram-бот — пульт управления домашним медиацентром [Kodi](https://kodi.tv/)
через его JSON-RPC API.

## Возможности

- `/start` — приветствие и главное меню
- `/movies` — список фильмов из библиотеки с пагинацией по 10 штук
- Поиск: просто напишите название фильма — бот найдёт совпадения
- Карточка фильма: постер, год, рейтинг, жанр, описание и кнопка «▶️ Смотреть»
- Пульт: ⏯ пауза/плей, ⏹ стоп, 🔊 громкость +/-
- `/now` — что сейчас играет (позиция, длительность, прогресс)
- Доступ только для user_id из белого списка `ALLOWED_USERS`

## 1. Включите JSON-RPC в Kodi

1. Откройте Kodi → **Настройки** (шестерёнка) → **Службы** → **Управление**.
2. Включите **«Разрешить удалённое управление по HTTP»**.
3. Задайте **порт** (по умолчанию `8080`), **имя пользователя** и **пароль** —
   они пойдут в `.env` как `KODI_PORT`, `KODI_LOGIN`, `KODI_PASSWORD`.
4. Там же включите **«Разрешить удалённое управление приложениям на других
   компьютерах»**, если бот будет работать не на той же машине, что Kodi.

Проверить, что API отвечает, можно из браузера или curl:

```bash
curl -u kodi:пароль -X POST http://<IP-Kodi>:8080/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"JSONRPC.Ping","id":1}'
# Ответ: {"id":1,"jsonrpc":"2.0","result":"pong"}
```

## 2. Получите токен бота у @BotFather

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram.
2. Команда `/newbot` → придумайте имя и username бота.
3. BotFather пришлёт токен вида `1234567890:AAAA...` — это `BOT_TOKEN`.

## 3. Узнайте свой Telegram user_id

Напишите боту [@userinfobot](https://t.me/userinfobot) (или
[@getmyid_bot](https://t.me/getmyid_bot)) — он ответит вашим числовым `id`.
Впишите его в `ALLOWED_USERS`. Несколько id разделяются запятой.

## 4. Запуск

```bash
# Клонируйте репозиторий и перейдите в него
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Создайте .env из примера и заполните своими значениями
cp .env.example .env

python bot.py
```

Бот должен работать в одной сети с Kodi (или иметь к нему сетевой доступ) —
например, на том же мини-ПК/Raspberry Pi, где крутится медиацентр.

## Структура проекта

```
bot.py            — точка входа, запуск polling
kodi_client.py    — async-обёртка над JSON-RPC API Kodi
config.py         — загрузка настроек из .env (pydantic + python-dotenv)
keyboards.py      — инлайн-клавиатуры
middlewares.py    — белый список пользователей
handlers/
  common.py       — /start, главное меню
  movies.py       — список, поиск, карточка, запуск фильма
  player.py       — /now и кнопки пульта
```

## Безопасность

- Все секреты — только в `.env` (файл в `.gitignore`, в репозитории лежит
  лишь `.env.example`).
- Middleware отклоняет любые сообщения от пользователей не из `ALLOWED_USERS`.
- При недоступности Kodi бот не падает, а сообщает об этом пользователю.
