#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegraph Parser — вытаскивает инфу из статей telegra.ph
по словам, фразам, regex-шаблонам и "символам" (почты, @ники, t.me, кошельки, коды...).

Что умеет:
  * fetch    — скачать одну статью (через официальный Telegraph API, fallback на HTML)
  * add      — добавить статьи в локальную базу (articles_db.json)
  * crawl    — обойти telegra.ph по ссылкам внутри статей (BFS) и нарастить базу
  * search   — искать по словам/фразам/regex, режимы OR/AND, выдаёт КОНТЕКСТНЫЕ сниппеты
  * extract  — доставать "символы" по готовым или своим regex-шаблонам (email, @ник, t.me, wallet, code...)
  * menu     — интерактивное меню (запуск без аргументов / двойной клик по .exe)

Работает и как CLI (можно скриптовать), и как меню.
Прокси (опционально) — HTTP-прокси из proxies.txt, по одному на строку.

Зависимости: requests, beautifulsoup4
    pip install requests beautifulsoup4
"""
from __future__ import annotations

import os
import re
import sys
import csv
import json
import time
import random
import argparse
from typing import Dict, List, Tuple, Optional, Iterable
from urllib.parse import urlparse, urljoin

import requests

try:
    from bs4 import BeautifulSoup
    HAVE_BS4 = True
except Exception:
    HAVE_BS4 = False


# --------------------- где живут файлы (рядом с .exe/скриптом) -------------- #
def _app_dir() -> str:
    if getattr(sys, "frozen", False):          # собрано в exe через PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _app_dir()


def _p(name: str) -> str:
    return os.path.join(APP_DIR, name)


DB_FILE = _p("articles_db.json")
SEED_FILE = _p("urls_seed.txt")
KEYWORDS_FILE = _p("keywords.txt")
PATTERNS_FILE = _p("patterns.txt")
PROXIES_FILE = _p("proxies.txt")
RESULTS_CSV = _p("results.csv")
EXTRACT_CSV = _p("extracted.csv")

# ------------------------------- настройки --------------------------------- #
TIMEOUT = 25
RETRIES = 3
BASE_DELAY_RANGE = (0.8, 2.2)
CRAWL_MAX_PAGES = 300
CRAWL_MAX_NEW_PER_PAGE = 40
SNIPPET_RADIUS = 90          # сколько символов контекста слева/справа от совпадения
API_BASE = "https://api.telegra.ph/getPage/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0 Safari/537.36",
]

# Готовые шаблоны для extract ("символы"). Своё можно добавить в patterns.txt или через --regex.
BUILTIN_PATTERNS: Dict[str, str] = {
    "email":    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
    "tg":       r"(?<![\w@])@[A-Za-z0-9_]{4,32}",                 # @username
    "tme":      r"https?://t\.me/[A-Za-z0-9_+/\-]+",              # ссылки t.me
    "url":      r"https?://[^\s<>\"')]+",
    "phone":    r"(?<!\d)(?:\+?\d[\d\-\s()]{8,}\d)(?!\d)",
    "ip":       r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "btc":      r"\b(?:bc1[a-z0-9]{25,90}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
    "eth":      r"\b0x[a-fA-F0-9]{40}\b",
    "trx":      r"\bT[A-Za-z0-9]{33}\b",                          # TRON-адрес
    "code":     r"\b[A-Z0-9]{3,}(?:-[A-Z0-9]{3,})+\b",           # ключи/промокоды типа XXXX-XXXX
    "hashtag":  r"(?<!\w)#[A-Za-z0-9_Ѐ-ӿ]{2,}",
}


# ============================= КРАСОТА (UI) ================================= #
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


USE_COLOR = True


def _init_color() -> None:
    """Включает ANSI-цвета (в т.ч. на Windows) и отключает их, если вывод не в консоль."""
    global USE_COLOR
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        USE_COLOR = False
    if os.name == "nt":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)   # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        except Exception:
            USE_COLOR = False


def c(text: str, *codes: str) -> str:
    if not USE_COLOR or not codes:
        return text
    return "".join(codes) + text + C.RESET


def banner() -> None:
    line = "═" * 46
    print()
    print(c("  ╔" + line + "╗", C.CYAN))
    print(c("  ║", C.CYAN) + c("           T E L E G R A P H   P A R S E R", C.BOLD, C.CYAN)
          + c("    ║", C.CYAN))
    print(c("  ╚" + line + "╝", C.CYAN))
    print(c("    поиск и извлечение инфы из telegra.ph", C.GRAY))


def section(title: str) -> None:
    print("\n" + c("▎", C.CYAN) + c(f" {title}", C.BOLD))


def ok(msg: str) -> None:
    print(c("  ✓ ", C.GREEN) + msg)


def warn(msg: str) -> None:
    print(c("  ! ", C.YELLOW) + msg)


def err(msg: str) -> None:
    print(c("  ✗ ", C.RED) + msg)


def info(msg: str) -> None:
    print(c("  · ", C.GRAY) + msg)


# ------------------------------- утилиты ----------------------------------- #
def jitter_sleep(a: float = BASE_DELAY_RANGE[0], b: float = BASE_DELAY_RANGE[1]) -> None:
    time.sleep(random.uniform(a, b))


def rand_headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "close",
    }


def is_telegra(url: str) -> bool:
    try:
        return urlparse(url.strip()).netloc.lower().endswith("telegra.ph")
    except Exception:
        return False


def norm_url(u: str) -> str:
    u = (u or "").strip()
    if "#" in u:
        u = u.split("#", 1)[0]
    return u.rstrip("/")


def telegraph_path(url: str) -> Optional[str]:
    """Из https://telegra.ph/Some-Title-01-02 -> Some-Title-01-02 (для API)."""
    try:
        p = urlparse(norm_url(url)).path.lstrip("/")
        return p or None
    except Exception:
        return None


def mask_proxy(p: str) -> str:
    return re.sub(r"(https?://[^:/@]+:)([^@]+)(@)", r"\1***\3", p)


def read_lines(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]


# ------- дефолтные конфиги: создаются сами при первом запуске --------------- #
DEFAULT_FILES: Dict[str, str] = {
    KEYWORDS_FILE: (
        "# Ключевые слова/фразы для команды search.\n"
        "# MODE=OR  -> статья подходит, если найдено ХОТЯ БЫ одно слово\n"
        "# MODE=AND -> статья подходит, только если найдены ВСЕ слова\n"
        "MODE=OR\n"
        "rust\n"
        "steam\n"
        "drops\n"
    ),
    PATTERNS_FILE: (
        "# Свои regex-шаблоны для команды extract.\n"
        "# Формат:  имя = регулярка       например:   promo = [A-Z]{3,}-\\d{4}-[A-Z]+\n"
        "# Встроенные (через --type): email, tg, tme, url, phone, ip, btc, eth, trx, code, hashtag\n"
        "# promo = [A-Z]{3,}-\\d{2,4}-[A-Z0-9]+\n"
    ),
    SEED_FILE: "# По одной telegra.ph ссылке на строку — стартовые статьи для add/crawl\n",
    PROXIES_FILE: (
        "# HTTP-прокси, по одному на строку (опционально)\n"
        "# ip:port\n"
        "# user:pass@ip:port\n"
    ),
}


def ensure_files() -> None:
    for path, content in DEFAULT_FILES.items():
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass


# ------------------------------- прокси ------------------------------------ #
def read_proxies() -> List[str]:
    out: List[str] = []
    for line in read_lines(PROXIES_FILE):
        line = line.strip('"').strip("'")
        if not re.match(r"^https?://", line, flags=re.I):
            line = "http://" + line
        out.append(line)
    return out


class ProxyPool:
    """Простой пул: по кругу отдаёт живые прокси, sticky на несколько запросов."""

    def __init__(self, proxies: List[str], sticky: int = 10):
        self.all = list(proxies)
        self.alive: List[str] = list(proxies)
        self.sticky = max(1, sticky)
        self._current: Optional[str] = None
        self._left = 0

    def _rotate(self) -> None:
        self._current = random.choice(self.alive) if self.alive else None
        self._left = self.sticky if self._current else 0

    def get(self) -> Tuple[Optional[Dict[str, str]], str]:
        if not self._current or self._left <= 0:
            self._rotate()
        if not self._current:
            return None, "DIRECT"
        self._left -= 1
        p = self._current
        return {"http": p, "https": p}, mask_proxy(p)

    def drop(self, proxy_label: str) -> None:
        if self._current and mask_proxy(self._current) == proxy_label:
            try:
                self.alive.remove(self._current)
            except ValueError:
                pass
            self._current = None
            self._left = 0


# ------------------------------- сеть -------------------------------------- #
def http_get(url: str, pool: ProxyPool, expect_json: bool = False):
    last_err: Optional[Exception] = None
    for attempt in range(1, RETRIES + 1):
        proxy, label = pool.get()
        try:
            r = requests.get(url, headers=rand_headers(), proxies=proxy, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json() if expect_json else r.text
        except Exception as e:
            last_err = e
            pool.drop(label)
            info(f"retry {attempt}/{RETRIES} [{label}] {e}")
            time.sleep((attempt ** 2) * random.uniform(0.6, 1.4))
    raise last_err  # type: ignore


# ---------------------- парсинг статьи (API + HTML) ------------------------ #
def _walk_nodes(nodes: Iterable, texts: List[str], links: List[str]) -> None:
    """Рекурсивно обходит content-дерево Telegraph API и собирает текст + ссылки."""
    for node in nodes:
        if isinstance(node, str):
            if node.strip():
                texts.append(node)
            continue
        if not isinstance(node, dict):
            continue
        tag = node.get("tag")
        if tag == "a":
            href = (node.get("attrs") or {}).get("href", "")
            if href:
                links.append(href)
        children = node.get("children")
        if children:
            _walk_nodes(children, texts, links)
        if tag in ("p", "h1", "h2", "h3", "h4", "li", "blockquote", "figcaption", "br"):
            texts.append("\n")


def parse_via_api(url: str, pool: ProxyPool) -> Optional[Tuple[str, str, List[str]]]:
    path = telegraph_path(url)
    if not path:
        return None
    try:
        data = http_get(API_BASE + path + "?return_content=true", pool, expect_json=True)
    except Exception:
        return None
    if not isinstance(data, dict) or not data.get("ok"):
        return None
    res = data.get("result") or {}
    title = (res.get("title") or "").strip()
    texts: List[str] = []
    links: List[str] = []
    _walk_nodes(res.get("content") or [], texts, links)
    text = re.sub(r"\n{2,}", "\n", "".join(texts)).strip()
    return title, text, _clean_links(links)


def parse_via_html(url: str, pool: ProxyPool) -> Tuple[str, str, List[str]]:
    if not HAVE_BS4:
        raise RuntimeError("bs4 не установлен, а API не сработал. pip install beautifulsoup4")
    html = http_get(url, pool)
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.find("h1")
    title = title_el.get_text(" ", strip=True) if title_el else ""
    article = soup.find("article") or soup
    parts = []
    for el in article.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "figcaption"]):
        t = el.get_text(" ", strip=True)
        if t:
            parts.append(t)
    text = "\n".join(parts).strip()
    links = [a.get("href", "") for a in soup.select("a[href]")]
    return title, text, _clean_links(links)


def _clean_links(links: List[str]) -> List[str]:
    seen, out = set(), []
    for href in links:
        href = (href or "").strip()
        if not href:
            continue
        if href.startswith("/"):
            href = urljoin("https://telegra.ph", href)
        href = norm_url(href)
        if is_telegra(href) and href not in seen:
            seen.add(href)
            out.append(href)
        if len(out) >= CRAWL_MAX_NEW_PER_PAGE:
            break
    return out


def parse_article(url: str, pool: ProxyPool) -> Tuple[str, str, List[str]]:
    """Сначала пробуем API (чисто и надёжно), потом HTML."""
    via_api = parse_via_api(url, pool)
    if via_api is not None:
        return via_api
    return parse_via_html(url, pool)


# ------------------------------- база -------------------------------------- #
def load_db() -> Dict[str, dict]:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_db(db: Dict[str, dict]) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def add_urls(urls: List[str], db: Dict[str, dict], pool: ProxyPool, force: bool = False) -> int:
    added = 0
    for u in urls:
        u = norm_url(u)
        if not is_telegra(u):
            warn(f"не telegra.ph: {u}")
            continue
        if u in db and not force:
            continue
        try:
            title, text, _ = parse_article(u, pool)
            db[u] = {"title": title, "text": text}
            added += 1
            ok(f"{c(title[:70] or '(без заголовка)', C.BOLD)}  {c(u, C.GRAY)}")
        except Exception as e:
            err(f"{u}: {e}")
        jitter_sleep()
    return added


def crawl(seeds: List[str], db: Dict[str, dict], pool: ProxyPool, max_pages: int) -> int:
    queue: List[str] = []
    seen = set()
    for s in seeds:
        s = norm_url(s)
        if is_telegra(s) and s not in seen:
            seen.add(s)
            queue.append(s)
    added = visited = 0
    while queue and visited < max_pages:
        url = queue.pop(0)
        visited += 1
        try:
            title, text, links = parse_article(url, pool)
            if url not in db:
                db[url] = {"title": title, "text": text}
                added += 1
                ok(f"{c(title[:60] or '(no title)', C.BOLD)}  {c(url, C.GRAY)}")
            for lk in links:
                if lk not in seen:
                    seen.add(lk)
                    queue.append(lk)
        except Exception as e:
            err(f"{url}: {e}")
        jitter_sleep()
        if visited % 25 == 0:
            save_db(db)
            info(f"visited={visited} added={added} queue={len(queue)}")
    return added


# ------------------------------ поиск -------------------------------------- #
def read_keywords() -> Tuple[str, List[str]]:
    mode = "OR"
    words: List[str] = []
    for line in read_lines(KEYWORDS_FILE):
        if line.upper().startswith("MODE="):
            m = line.split("=", 1)[1].strip().upper()
            if m in ("OR", "AND"):
                mode = m
            continue
        words.append(line)
    seen, out = set(), []
    for w in words:
        k = w.lower()
        if k not in seen:
            seen.add(k)
            out.append(w)
    return mode, out


def build_matchers(terms: List[str], regex: bool, ignore_case: bool) -> List[Tuple[str, re.Pattern]]:
    flags = re.IGNORECASE if ignore_case else 0
    matchers = []
    for t in terms:
        pat = t if regex else re.escape(t)
        try:
            matchers.append((t, re.compile(pat, flags)))
        except re.error as e:
            err(f"regex '{t}': {e}")
    return matchers


def make_snippet(text: str, m: re.Match) -> str:
    start = max(0, m.start() - SNIPPET_RADIUS)
    end = min(len(text), m.end() + SNIPPET_RADIUS)
    snippet = re.sub(r"\s+", " ", text[start:end].replace("\n", " ")).strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    matched = m.group(0).strip()
    if USE_COLOR and matched:
        try:
            snippet = re.sub(re.escape(matched),
                             lambda mm: c(mm.group(0), C.BOLD, C.YELLOW),
                             snippet, flags=re.IGNORECASE)
        except re.error:
            pass
    return f"{prefix}{snippet}{suffix}"


def search_db(db: Dict[str, dict], terms: List[str], mode: str,
              regex: bool, ignore_case: bool) -> List[dict]:
    matchers = build_matchers(terms, regex, ignore_case)
    if not matchers:
        return []
    results = []
    for url, item in db.items():
        content = (item.get("title", "") + "\n" + item.get("text", ""))
        hit_terms = set()
        snippets: List[str] = []
        for term, pat in matchers:
            m = pat.search(content)
            if m:
                hit_terms.add(term)
                if len(snippets) < 5:
                    snippets.append(f"{c('['+term+']', C.CYAN)} {make_snippet(content, m)}")
        ok_match = (len(hit_terms) == len(matchers)) if mode == "AND" else bool(hit_terms)
        if ok_match:
            results.append({
                "url": url,
                "title": item.get("title", ""),
                "matched": sorted(hit_terms),
                "snippets": snippets,
            })
    results.sort(key=lambda r: (-len(r["matched"]), (r["title"] or "").lower()))
    return results


def extract_db(db: Dict[str, dict], patterns: Dict[str, str], ignore_case: bool) -> List[dict]:
    compiled = []
    flags = re.IGNORECASE if ignore_case else 0
    for name, pat in patterns.items():
        try:
            compiled.append((name, re.compile(pat, flags)))
        except re.error as e:
            err(f"regex '{name}': {e}")
    rows = []
    for url, item in db.items():
        content = (item.get("title", "") + "\n" + item.get("text", ""))
        for name, pat in compiled:
            found, seen = [], set()
            for m in pat.finditer(content):
                val = m.group(0).strip()
                if val and val not in seen:
                    seen.add(val)
                    found.append(val)
            for val in found:
                rows.append({"url": url, "type": name, "value": val,
                             "title": item.get("title", "")})
    return rows


def read_patterns_file() -> Dict[str, str]:
    """patterns.txt: строки вида  name = regex  (или просто regex -> имя pN)."""
    out: Dict[str, str] = {}
    n = 0
    for line in read_lines(PATTERNS_FILE):
        if "=" in line and not line.lstrip().startswith("("):
            name, pat = line.split("=", 1)
            out[name.strip()] = pat.strip()
        else:
            n += 1
            out[f"p{n}"] = line
    return out


# ------------------------------ экспорт ------------------------------------ #
def export_search(rows: List[dict], path: str = RESULTS_CSV) -> str:
    _strip = re.compile(r"\033\[[0-9;]*m")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "title", "matched", "snippets"])
        for r in rows:
            snips = "  ||  ".join(_strip.sub("", s) for s in r["snippets"])
            w.writerow([r["url"], r["title"], "; ".join(r["matched"]), snips])
    return path


def export_extract(rows: List[dict], path: str = EXTRACT_CSV) -> str:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type", "value", "url", "title"])
        for r in rows:
            w.writerow([r["type"], r["value"], r["url"], r["title"]])
    return path


# ------------------------------ печать ------------------------------------- #
def print_search(rows: List[dict]) -> None:
    if not rows:
        warn("Ничего не найдено.")
        return
    section(f"Совпадений: {len(rows)}")
    for i, r in enumerate(rows, 1):
        print(f"\n{c(str(i)+'.', C.BOLD, C.GREEN)} {c(r['title'] or '(без заголовка)', C.BOLD)}")
        print(f"   {c(r['url'], C.BLUE)}")
        print(f"   {c('совпало:', C.GRAY)} {', '.join(c(t, C.YELLOW) for t in r['matched'])}")
        for s in r["snippets"]:
            print(f"     {c('›', C.GRAY)} {s}")


def print_extract(rows: List[dict]) -> None:
    if not rows:
        warn("Ничего не извлечено.")
        return
    by_type: Dict[str, List[str]] = {}
    for r in rows:
        by_type.setdefault(r["type"], []).append(r["value"])
    section(f"Извлечено значений: {len(rows)}")
    for t, vals in by_type.items():
        uniq = list(dict.fromkeys(vals))
        print(f"\n{c('['+t+']', C.CYAN, C.BOLD)} {c('всего '+str(len(uniq)), C.GRAY)}")
        for v in uniq[:50]:
            print(f"   {v}")
        if len(uniq) > 50:
            info(f"… ещё {len(uniq) - 50}")


# ------------------------------ CLI ---------------------------------------- #
def make_pool() -> ProxyPool:
    proxies = read_proxies()
    if proxies:
        info(f"прокси: {len(proxies)} (DIRECT как fallback)")
    else:
        info("прокси: нет (напрямую)")
    return ProxyPool(proxies)


def cmd_fetch(args) -> None:
    pool = make_pool()
    title, text, links = parse_article(args.url, pool)
    section(title or "(без заголовка)")
    info(f"telegra.ph-ссылок внутри: {len(links)}")
    print(c("─" * 54, C.GRAY))
    print(text[:args.limit])
    if len(text) > args.limit:
        info(f"обрезано, всего {len(text)} символов (--limit чтобы больше)")


def cmd_add(args) -> None:
    pool = make_pool()
    db = load_db()
    urls = list(args.urls) if args.urls else read_lines(SEED_FILE)
    if not urls:
        warn(f"Нет URL. Передай аргументом или заполни {os.path.basename(SEED_FILE)}")
        return
    section("Добавление в базу")
    added = add_urls(urls, db, pool, force=args.force)
    save_db(db)
    ok(f"добавлено: {added}  ·  в базе: {len(db)}")


def cmd_crawl(args) -> None:
    pool = make_pool()
    db = load_db()
    seeds = list(args.urls) if args.urls else read_lines(SEED_FILE)
    if not seeds:
        warn(f"Нет стартовых URL. Заполни {os.path.basename(SEED_FILE)} или передай аргументом.")
        return
    section("Crawl")
    added = crawl(seeds, db, pool, args.max_pages)
    save_db(db)
    ok(f"crawl добавил: {added}  ·  в базе: {len(db)}")


def cmd_search(args) -> None:
    db = load_db()
    if not db:
        warn(f"База пуста. Сначала add/crawl. ({os.path.basename(DB_FILE)})")
        return
    if args.terms:
        terms, mode = list(args.terms), ("AND" if args.all else "OR")
    else:
        mode, terms = read_keywords()
        if args.all:
            mode = "AND"
    if not terms:
        warn(f"Нет ключевых слов. Передай аргументом или заполни {os.path.basename(KEYWORDS_FILE)}")
        return
    info(f"MODE={mode}  regex={args.regex}  слов={len(terms)}  статей={len(db)}")
    rows = search_db(db, terms, mode, args.regex, not args.case)
    print_search(rows)
    if rows:
        ok(f"CSV: {export_search(rows)}")


def cmd_extract(args) -> None:
    db = load_db()
    if not db:
        warn(f"База пуста. Сначала add/crawl. ({os.path.basename(DB_FILE)})")
        return
    patterns: Dict[str, str] = {}
    if args.regex:
        for i, pat in enumerate(args.regex, 1):
            patterns[f"custom{i}"] = pat
    if args.type:
        for t in args.type:
            if t in BUILTIN_PATTERNS:
                patterns[t] = BUILTIN_PATTERNS[t]
            else:
                warn(f"нет встроенного шаблона '{t}'. Доступны: {', '.join(BUILTIN_PATTERNS)}")
    patterns.update(read_patterns_file())
    if not patterns:
        patterns = dict(BUILTIN_PATTERNS)
        info("шаблоны не заданы — использую все встроенные.")
    rows = extract_db(db, patterns, not args.case)
    print_extract(rows)
    if rows:
        ok(f"CSV: {export_extract(rows)}")


# --------------------------- интерактивное меню ---------------------------- #
def _menu_prompt(text: str) -> str:
    return input(c("  » ", C.CYAN) + text + ": ").strip()


def cmd_menu(_args) -> None:
    pool = make_pool()
    db = load_db()
    while True:
        banner()
        print(c(f"  база: {len(db)} статей", C.GRAY) +
              c(f"   ·   папка: {APP_DIR}", C.GRAY))
        print()
        items = [
            ("1", "Добавить URL(ы) в базу"),
            ("2", "Добавить из urls_seed.txt"),
            ("3", "CRAWL из urls_seed.txt (расти по ссылкам)"),
            ("4", "Поиск по keywords.txt"),
            ("5", "Extract (email / @ник / t.me / кошельки / коды…)"),
            ("6", "Скачать и показать одну статью"),
            ("0", "Выход"),
        ]
        for key, label in items:
            print(f"   {c(key, C.BOLD, C.GREEN)}  {label}")
        choice = _menu_prompt("выбор")
        try:
            if choice == "1":
                u = _menu_prompt("URL(ы) через пробел").split()
                add_urls(u, db, pool)
                save_db(db)
            elif choice == "2":
                add_urls(read_lines(SEED_FILE), db, pool)
                save_db(db)
            elif choice == "3":
                seeds = read_lines(SEED_FILE)
                if seeds:
                    crawl(seeds, db, pool, CRAWL_MAX_PAGES)
                    save_db(db)
                else:
                    warn(f"{os.path.basename(SEED_FILE)} пуст.")
            elif choice == "4":
                mode, terms = read_keywords()
                rows = search_db(db, terms, mode, regex=False, ignore_case=True)
                print_search(rows)
                if rows:
                    ok(f"CSV: {export_search(rows)}")
            elif choice == "5":
                pats = read_patterns_file() or dict(BUILTIN_PATTERNS)
                rows = extract_db(db, pats, ignore_case=True)
                print_extract(rows)
                if rows:
                    ok(f"CSV: {export_extract(rows)}")
            elif choice == "6":
                u = _menu_prompt("telegra.ph URL")
                title, text, links = parse_article(u, pool)
                section(title or "(без заголовка)")
                info(f"ссылок: {len(links)}")
                print(text[:2000])
            elif choice == "0":
                print(c("  пока!", C.CYAN))
                break
            else:
                warn("не понял, выбери цифру из меню.")
        except KeyboardInterrupt:
            print()
            break
        except Exception as e:
            err(str(e))
        input(c("\n  Enter — продолжить…", C.GRAY))
        print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="telegraph_parser",
        description="Парсер telegra.ph: поиск по словам/regex и извлечение 'символов'.",
    )
    sub = p.add_subparsers(dest="cmd")

    f = sub.add_parser("fetch", help="скачать и показать одну статью")
    f.add_argument("url")
    f.add_argument("--limit", type=int, default=4000, help="сколько символов текста показать")
    f.set_defaults(func=cmd_fetch)

    a = sub.add_parser("add", help="добавить статьи в базу")
    a.add_argument("urls", nargs="*", help="URL(ы); если пусто — берёт из urls_seed.txt")
    a.add_argument("--force", action="store_true", help="перекачать даже если уже в базе")
    a.set_defaults(func=cmd_add)

    cr = sub.add_parser("crawl", help="обход по ссылкам внутри статей")
    cr.add_argument("urls", nargs="*", help="стартовые URL; если пусто — из urls_seed.txt")
    cr.add_argument("--max-pages", type=int, default=CRAWL_MAX_PAGES)
    cr.set_defaults(func=cmd_crawl)

    s = sub.add_parser("search", help="поиск по словам/фразам/regex")
    s.add_argument("terms", nargs="*", help="слова/фразы; если пусто — из keywords.txt")
    s.add_argument("--regex", action="store_true", help="считать термины regex-шаблонами")
    s.add_argument("--all", action="store_true", help="режим AND (по умолчанию OR)")
    s.add_argument("--case", action="store_true", help="учитывать регистр")
    s.set_defaults(func=cmd_search)

    e = sub.add_parser("extract", help="извлечь символы по шаблонам")
    e.add_argument("--type", action="append",
                   help=f"встроенный шаблон ({', '.join(BUILTIN_PATTERNS)}); можно несколько")
    e.add_argument("--regex", action="append", help="свой regex; можно несколько")
    e.add_argument("--case", action="store_true", help="учитывать регистр")
    e.set_defaults(func=cmd_extract)

    m = sub.add_parser("menu", help="интерактивное меню")
    m.set_defaults(func=cmd_menu)

    return p


def main() -> None:
    _init_color()
    ensure_files()
    parser = build_parser()
    args = parser.parse_args()
    try:
        if not getattr(args, "func", None):
            cmd_menu(args)         # без аргументов / двойной клик по .exe -> меню
        else:
            args.func(args)
    except KeyboardInterrupt:
        print()
    except Exception as e:
        err(str(e))
        if getattr(sys, "frozen", False):
            input("\nEnter — закрыть…")   # чтобы окно .exe не схлопнулось на ошибке


if __name__ == "__main__":
    main()
