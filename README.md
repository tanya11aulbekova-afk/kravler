# Telegraph Parser

Свой парсер для [telegra.ph](https://telegra.ph): собирает статьи в локальную базу
и достаёт из них инфу **по словам, фразам, regex-шаблонам и «символам»**
(почты, `@ники`, ссылки `t.me`, кошельки, промокоды и т.д.).

Наследует идеи старого `telegraph_finder_v127`, но:
- тянет статьи через **официальный Telegraph API** (чистый текст, надёжнее HTML-скрапинга), с fallback на HTML;
- поиск отдаёт **контекстные сниппеты** (кусок текста вокруг совпадения), а не всю статью;
- есть **regex-поиск** и **extract по шаблонам** — то самое «доставать по ключевым символам»;
- работает и как **CLI** (можно скриптовать), и как **меню**.

## Установка

```bash
pip install -r requirements.txt        # requests + beautifulsoup4
python telegraph_parser.py             # без аргументов -> меню
```

## Как это работает

1. Наполняешь базу статьями: `add` (по ссылкам) или `crawl` (обход по ссылкам внутри статей).
2. Всё складывается в `articles_db.json`.
3. Ищешь по базе: `search` (слова/regex) или `extract` (символы по шаблонам).

## Команды

```bash
# Показать одну статью (текст + сколько внутри telegra.ph-ссылок)
python telegraph_parser.py fetch https://telegra.ph/Some-Page-01-02

# Добавить статьи в базу (или из urls_seed.txt, если без аргументов)
python telegraph_parser.py add https://telegra.ph/A-01-01 https://telegra.ph/B-02-02

# Обойти по ссылкам внутри статей и нарастить базу (BFS)
python telegraph_parser.py crawl https://telegra.ph/Start-01-01 --max-pages 300

# Поиск по словам. Без аргументов берёт слова и режим из keywords.txt
python telegraph_parser.py search rust steam drops          # OR (любое слово)
python telegraph_parser.py search rust steam --all          # AND (все слова)
python telegraph_parser.py search "RUST-\d{4}-[A-Z]+" --regex   # regex
python telegraph_parser.py search Rust --case               # с учётом регистра

# Извлечь "символы" по шаблонам
python telegraph_parser.py extract                          # все встроенные шаблоны
python telegraph_parser.py extract --type email --type tg   # только почты и @ники
python telegraph_parser.py extract --regex "[A-Z]{3,}-\d{4}-[A-Z]+"   # свой regex
```

Результаты поиска пишутся в `results.csv`, извлечённые значения — в `extracted.csv`.

## Встроенные шаблоны для `extract`

| тип | что ловит |
|-----|-----------|
| `email` | почтовые адреса |
| `tg` | телеграм-ники `@username` |
| `tme` | ссылки `https://t.me/...` |
| `url` | любые http(s)-ссылки |
| `phone` | номера телефонов |
| `ip` | IPv4-адреса |
| `btc` / `eth` / `trx` | крипто-кошельки (Bitcoin / Ethereum / TRON) |
| `code` | ключи/промокоды вида `XXXX-XXXX-XXXX` |
| `hashtag` | хэштеги `#тег` |

Свои шаблоны — в `patterns.txt` (`имя = регулярка`) или прямо в командной строке через `--regex`.

## Файлы

| файл | зачем |
|------|-------|
| `telegraph_parser.py` | сам парсер |
| `keywords.txt` | слова и режим (OR/AND) для `search` |
| `patterns.txt` | свои regex-шаблоны для `extract` |
| `urls_seed.txt` | стартовые telegra.ph-ссылки для `add`/`crawl` |
| `proxies.txt` | HTTP-прокси (опционально) |
| `articles_db.json` | локальная база статей (создаётся автоматически) |

## Прокси

Если нужны — по одному на строку в `proxies.txt` (`ip:port` или `user:pass@ip:port`).
Пул подставляет их по кругу, дохлые выкидывает, без прокси идёт напрямую.

## Заметка

Парсер работает только с публичными статьями telegra.ph. Используй его ответственно
и в рамках закона и правил площадки.
