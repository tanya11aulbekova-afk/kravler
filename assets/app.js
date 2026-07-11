/* Kravler — данные и рендеринг (демо-каталог) */

const CATEGORIES = [
  { id: 'accounts', name: 'Аккаунты' },
  { id: 'currency', name: 'Валюта' },
  { id: 'keys',     name: 'Ключи и гифты' },
  { id: 'items',    name: 'Скины' },
  { id: 'services', name: 'Буст' },
  { id: 'topup',    name: 'Пополнение' },
];

const GAMES = [
  { id: 'cs2',      name: 'CS2',            mono: 'CS', count: 3210 },
  { id: 'dota2',    name: 'Dota 2',         mono: 'D2', count: 2480 },
  { id: 'genshin',  name: 'Genshin Impact', mono: 'GI', count: 1890 },
  { id: 'fortnite', name: 'Fortnite',       mono: 'FN', count: 1540 },
  { id: 'brawl',    name: 'Brawl Stars',    mono: 'BS', count: 1120 },
  { id: 'roblox',   name: 'Roblox',         mono: 'RB', count: 980 },
  { id: 'valorant', name: 'Valorant',       mono: 'VA', count: 860 },
  { id: 'steam',    name: 'Steam',          mono: 'ST', count: 840 },
  { id: 'wot',      name: 'World of Tanks', mono: 'WT', count: 760 },
  { id: 'mc',       name: 'Minecraft',      mono: 'MC', count: 720 },
];

const OFFERS = [
  { id: 1,  game: 'cs2',      cat: 'items',    name: '★ Karambit | Doppler Factory New', price: 84500, seller: 'VeteranTrade', rating: 4.9, deals: 2140, time: '5 мин',  featured: true,  badge: 'Топ',
    desc: 'Нож Karambit Doppler Phase 2, Factory New, float 0.008. Передача через обмен Steam сразу после подтверждения сделки. Инвентарь открыт для проверки.' },
  { id: 2,  game: 'steam',    cat: 'topup',    name: 'Пополнение кошелька Steam RU/KZ',  price: 100,   priceFrom: true, seller: 'FastWallet', rating: 5.0, deals: 18320, time: '2 мин', featured: true, badge: 'Хит',
    desc: 'Пополнение кошелька Steam на любую сумму от 100 ₽. Комиссия уже включена в цену. Зачисление в течение пары минут, работаем круглосуточно.' },
  { id: 3,  game: 'genshin',  cat: 'accounts', name: 'Аккаунт AR 60 · 14 легендарных',   price: 24900, seller: 'PrimoStore',   rating: 4.8, deals: 640,  time: '15 мин', featured: true,
    desc: 'Аккаунт Genshin Impact, ранг приключений 60. 14 пятизвёздочных персонажей, включая лимитированных. Смена всех данных, полный доступ, почта в комплекте.' },
  { id: 4,  game: 'dota2',    cat: 'services', name: 'Буст MMR 1000–5000 · Immortal',    price: 3500,  seller: 'AscendBoost',  rating: 4.9, deals: 1105, time: '1 час',  featured: true,
    desc: 'Профессиональный буст рейтинга от игроков Immortal. Цена указана за 100 MMR. Играем без читов и скриптов, стрим по запросу, VPN вашего региона.' },
  { id: 5,  game: 'fortnite', cat: 'accounts', name: 'Аккаунт 120+ скинов · OG',         price: 15900, seller: 'SkinVault',    rating: 4.7, deals: 890,  time: '20 мин', featured: true, badge: 'OG',
    desc: 'Аккаунт Fortnite со 120+ скинами, включая редкие из первых сезонов. Полный доступ, смена почты. Подробный список скинов вышлю по запросу.' },
  { id: 6,  game: 'brawl',    cat: 'topup',    name: 'Гемы 2000 + 170 бонусом',          price: 4990,  seller: 'GemDealer',    rating: 4.9, deals: 5430, time: '10 мин', featured: true,
    desc: 'Пополнение гемов через подарочную систему — вход в аккаунт не требуется. 2000 гемов + 170 бонусом. Работаем с RU и KZ регионами.' },
  { id: 7,  game: 'roblox',   cat: 'currency', name: 'Robux 10 000 через геймпасс',      price: 6200,  seller: 'BlockMarket',  rating: 4.8, deals: 3210, time: '30 мин', featured: true,
    desc: '10 000 Robux через геймпасс. Комиссия платформы компенсирована. Выдача в течение 30 минут после подтверждения сделки.' },
  { id: 8,  game: 'valorant', cat: 'accounts', name: 'Аккаунт Immortal 3 · EU · 40 скинов', price: 11400, seller: 'RadiantShop', rating: 4.6, deals: 410, time: '25 мин', featured: true,
    desc: 'Аккаунт Valorant с рангом Immortal 3, регион EU. 40+ скинов, включая Reaver Vandal. Полный доступ и смена данных.' },
  { id: 9,  game: 'wot',      cat: 'currency', name: 'Золото 25 000 · Lesta RU',         price: 5100,  seller: 'TankTreasury', rating: 4.9, deals: 7650, time: '8 мин',
    desc: '25 000 золота на ваш аккаунт World of Tanks (Lesta RU). Зачисление подарком, аккаунт не требуется. Скидки на объёмы от 50 000.' },
  { id: 10, game: 'cs2',      cat: 'keys',     name: 'Prime Status · ключ активации',    price: 1290,  seller: 'KeyForge',     rating: 5.0, deals: 9840, time: '1 мин',
    desc: 'Ключ активации Prime Status для CS2. Моментальная выдача кода после оплаты. Регион — глобальный, активация без VPN.' },
  { id: 11, game: 'steam',    cat: 'keys',     name: 'Случайный ключ AAA-игры',          price: 390,   seller: 'KeyForge',     rating: 4.7, deals: 12100, time: '1 мин',
    desc: 'Случайный Steam-ключ из пула AAA-игр стоимостью от 1000 ₽. Моментальная выдача. Дубликаты в течение месяца заменяем бесплатно.' },
  { id: 12, game: 'genshin',  cat: 'topup',    name: 'Кристаллы 6480 + бонус ×2',        price: 7900,  seller: 'PrimoStore',   rating: 4.9, deals: 4470, time: '12 мин',
    desc: '6480 кристаллов сотворения с удвоением первой покупки. Пополнение через UID — вход в аккаунт не требуется.' },
  { id: 13, game: 'mc',       cat: 'accounts', name: 'Лицензия Java + Bedrock',          price: 2190,  seller: 'CraftKeys',    rating: 4.8, deals: 6320, time: '5 мин',
    desc: 'Полный доступ к аккаунту Microsoft с лицензией Minecraft Java & Bedrock. Смена почты и никнейма. Гарантия 90 дней.' },
  { id: 14, game: 'dota2',    cat: 'items',    name: 'Аркана PA · Manifold Paradox',     price: 8700,  seller: 'VeteranTrade', rating: 4.9, deals: 2140, time: '5 мин',
    desc: 'Manifold Paradox — аркана на Phantom Assassin. Передача обменом Steam, без ожидания. Возможен торг при покупке нескольких предметов.' },
  { id: 15, game: 'fortnite', cat: 'topup',    name: 'В-баксы 5000',                     price: 3290,  seller: 'SkinVault',    rating: 4.8, deals: 890,  time: '15 мин',
    desc: '5000 В-баксов через подарок с личного аккаунта. Требуется 48 часов в друзьях либо покупка через свой аккаунт с полным доступом.' },
  { id: 16, game: 'valorant', cat: 'services', name: 'Буст до Diamond · за дивизион',    price: 2900,  seller: 'AscendBoost',  rating: 4.9, deals: 1105, time: '2 часа',
    desc: 'Буст ранга до Diamond от игроков Radiant. Цена за дивизион. Играем на вашем аккаунте или в дуо — на выбор.' },
  { id: 17, game: 'cs2',      cat: 'accounts', name: 'Аккаунт 10 000 часов · Global Elite', price: 7400, seller: 'SkinVault', rating: 4.7, deals: 890, time: '20 мин',
    desc: 'Аккаунт CS2 с 10 000+ часов, звание Global Elite, Prime Status. Полный доступ, смена почты, чистая история без банов.' },
  { id: 18, game: 'wot',      cat: 'accounts', name: 'Аккаунт 15 топов · 60% побед',     price: 18700, seller: 'TankTreasury', rating: 4.9, deals: 7650, time: '25 мин',
    desc: 'Аккаунт World of Tanks с 15 топовыми машинами X уровня, процент побед 60%. Полный доступ и смена данных.' },
  { id: 19, game: 'roblox',   cat: 'keys',     name: 'Гифт-карта Roblox 25$',            price: 2450,  seller: 'BlockMarket',  rating: 4.8, deals: 3210, time: '3 мин',
    desc: 'Официальная подарочная карта Roblox номиналом 25$. Код выдаётся автоматически после оплаты. Регион — глобальный.' },
  { id: 20, game: 'brawl',    cat: 'accounts', name: 'Аккаунт 80+ бравлеров · 40к кубков', price: 9300, seller: 'GemDealer',  rating: 4.9, deals: 5430, time: '15 мин',
    desc: 'Аккаунт Brawl Stars: 80+ бравлеров, 40 000 кубков, редкие скины из сезонов. Привязка к вашей почте.' },
];

/* ---------- helpers ---------- */

const fmtPrice = (o) => (o.priceFrom ? 'от ' : '') + o.price.toLocaleString('ru-RU') + ' ₽';
const gameOf   = (id) => GAMES.find(g => g.id === id);
const catOf    = (id) => CATEGORIES.find(c => c.id === id);
const fmtNum   = (n) => n.toLocaleString('ru-RU');

function lotPlural(n) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return 'лот';
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return 'лота';
  return 'лотов';
}

function offerPlural(n) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return 'предложение';
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return 'предложения';
  return 'предложений';
}

/* ---------- shared header / footer ---------- */

function renderHeader(activeCat) {
  const cats = [{ id: '', name: 'Все игры' }, ...CATEGORIES]
    .map(c => `<a href="catalog.html${c.id ? '?cat=' + c.id : ''}" class="${(activeCat ?? '') === c.id ? 'on' : ''}">${c.name}</a>`)
    .join('');
  return `
    <div class="h-top">
      <a class="logo" href="index.html">KRAVLER</a>
      <form class="h-search" action="catalog.html">
        <input name="q" placeholder="Поиск по 12 400 товарам…">
        <button type="submit">Найти</button>
      </form>
      <div class="h-links"><a href="#" data-demo>Помощь</a><a href="#" data-demo>Войти</a></div>
      <a class="btn-sell" href="#" data-demo>+ Продать</a>
    </div>
    <div class="h-cats">${cats}</div>`;
}

function renderFooter() {
  return `
    <div class="footer-top">
      <div class="f-brand">
        <div class="logo">KRAVLER</div>
        <p>Маркетплейс игровых товаров: аккаунты, валюта, ключи, скины и услуги с гарантией сделки.</p>
      </div>
      <div class="footer-cols">
        <div class="footer-col">
          <h4>Каталог</h4>
          ${CATEGORIES.map(c => `<a href="catalog.html?cat=${c.id}">${c.name}</a>`).join('')}
        </div>
        <div class="footer-col">
          <h4>Покупателям</h4>
          <a href="index.html#how">Как проходит сделка</a>
          <a href="index.html#trust">Гарантии</a>
          <a href="#" data-demo>Поддержка</a>
        </div>
        <div class="footer-col">
          <h4>Продавцам</h4>
          <a href="#" data-demo>Начать продавать</a>
          <a href="#" data-demo>Комиссии</a>
          <a href="#" data-demo>Правила</a>
        </div>
      </div>
    </div>
    <div class="footer-bottom"><div class="wrap"><span>© 2026 Kravler. Маркетплейс игровых товаров.</span><a href="#top">Наверх ↑</a></div></div>`;
}

/* ---------- cards ---------- */

function offerCard(o) {
  const g = gameOf(o.game);
  const c = catOf(o.cat);
  return `
    <a class="card" href="product.html?id=${o.id}">
      ${o.badge ? `<span class="badge">${o.badge}</span>` : ''}
      <span class="c-tag">${g.name} <span>· ${c.name}</span></span>
      <h3>${o.name}</h3>
      <span class="c-seller"><span class="ava">${o.seller[0]}</span>${o.seller} · <i>★</i>&nbsp;${o.rating} · ${fmtNum(o.deals)} сделок</span>
      <span class="c-foot"><span class="price">${fmtPrice(o)}</span><span class="c-buy">Купить</span></span>
    </a>`;
}

function gameTile(g) {
  return `
    <a class="game" href="catalog.html?game=${g.id}">
      <span class="g-ico">${g.mono}</span>
      <b>${g.name}</b>
      <span>${fmtNum(g.count)}</span>
    </a>`;
}

/* ---------- renderers ---------- */

function renderGames(el, limit) {
  if (!el) return;
  el.innerHTML = GAMES.slice(0, limit || GAMES.length).map(gameTile).join('');
}

function renderOffers(el, offers) {
  if (!el) return;
  el.innerHTML = offers.map(offerCard).join('');
}

/* ---------- boot shared chrome ---------- */

document.addEventListener('DOMContentLoaded', () => {
  const header = document.querySelector('.site-header');
  if (header) header.innerHTML = renderHeader(header.dataset.cat);
  const footer = document.querySelector('.site-footer');
  if (footer) footer.innerHTML = renderFooter();
});

/* ---------- demo interactions ---------- */

document.addEventListener('click', (e) => {
  const demoLink = e.target.closest('[data-demo]');
  if (demoLink) {
    e.preventDefault();
    showToast('Это демо-версия — раздел в разработке');
  }
});

function showToast(text) {
  let t = document.querySelector('.toast');
  if (!t) {
    t = document.createElement('div');
    t.className = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = text;
  t.classList.add('toast-show');
  clearTimeout(t._hide);
  t._hide = setTimeout(() => t.classList.remove('toast-show'), 2600);
}
