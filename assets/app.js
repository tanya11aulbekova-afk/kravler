/* Kravler — данные и рендеринг (демо-каталог) */

const CATEGORIES = [
  { id: 'accounts', num: '01', name: 'Аккаунты',        note: 'Steam, Epic, Riot и другие' },
  { id: 'currency', num: '02', name: 'Игровая валюта',  note: 'Золото, кристаллы, кредиты' },
  { id: 'keys',     num: '03', name: 'Ключи и гифты',   note: 'Активация в один клик' },
  { id: 'items',    num: '04', name: 'Предметы и скины',note: 'Ножи, кейсы, редкие дропы' },
  { id: 'services', num: '05', name: 'Буст и услуги',   note: 'Ранги, календарь, фарм' },
  { id: 'topup',    num: '06', name: 'Пополнение',      note: 'Донат без входа в аккаунт' },
];

const GAMES = [
  { id: 'cs2',      name: 'CS2',            mono: 'CS' },
  { id: 'dota2',    name: 'Dota 2',         mono: 'D2' },
  { id: 'steam',    name: 'Steam',          mono: 'ST' },
  { id: 'genshin',  name: 'Genshin Impact', mono: 'GI' },
  { id: 'fortnite', name: 'Fortnite',       mono: 'FN' },
  { id: 'brawl',    name: 'Brawl Stars',    mono: 'BS' },
  { id: 'roblox',   name: 'Roblox',         mono: 'RB' },
  { id: 'valorant', name: 'Valorant',       mono: 'VA' },
  { id: 'wot',      name: 'World of Tanks', mono: 'WT' },
  { id: 'mc',       name: 'Minecraft',      mono: 'MC' },
];

const OFFERS = [
  { id: 1,  game: 'cs2',      cat: 'items',    name: '★ Karambit | Doppler FN',        price: 84500, seller: 'VeteranTrade', rating: 4.9, deals: 2140, time: '5 мин',  featured: true,
    desc: 'Нож Karambit Doppler Phase 2, Factory New, float 0.008. Передача через обмен Steam сразу после подтверждения сделки. Инвентарь открыт для проверки.' },
  { id: 2,  game: 'steam',    cat: 'topup',    name: 'Пополнение Steam · RU/KZ',        price: 1000,  seller: 'FastWallet',   rating: 5.0, deals: 18320, time: '2 мин', featured: true,
    desc: 'Пополнение кошелька Steam на любую сумму от 100 ₽. Комиссия уже включена в цену. Зачисление в течение пары минут, работаем круглосуточно.' },
  { id: 3,  game: 'genshin',  cat: 'accounts', name: 'Аккаунт AR 60 · 14 легендарок',   price: 24900, seller: 'PrimoStore',   rating: 4.8, deals: 640,  time: '15 мин', featured: true,
    desc: 'Аккаунт Genshin Impact, ранг приключений 60. 14 пятизвёздочных персонажей, включая лимитированных. Смена всех данных, полный доступ, почта в комплекте.' },
  { id: 4,  game: 'dota2',    cat: 'services', name: 'Буст MMR 1000–5000',              price: 3500,  seller: 'AscendBoost',  rating: 4.9, deals: 1105, time: '1 час',  featured: true,
    desc: 'Профессиональный буст рейтинга от игроков Immortal. Цена указана за 100 MMR. Играем без читов и скриптов, стрим по запросу, VPN вашего региона.' },
  { id: 5,  game: 'fortnite', cat: 'accounts', name: 'Аккаунт 120+ скинов · OG',        price: 15900, seller: 'SkinVault',    rating: 4.7, deals: 890,  time: '20 мин', featured: true,
    desc: 'Аккаунт Fortnite со 120+ скинами, включая редкие из первых сезонов. Полный доступ, смена почты. Подробный список скинов вышлю по запросу.' },
  { id: 6,  game: 'brawl',    cat: 'topup',    name: 'Гемы 2000 + бонус',               price: 4990,  seller: 'GemDealer',    rating: 4.9, deals: 5430, time: '10 мин', featured: true,
    desc: 'Пополнение гемов через подарочную систему — вход в аккаунт не требуется. 2000 гемов + 170 бонусом. Работаем с RU и KZ регионами.' },
  { id: 7,  game: 'roblox',   cat: 'currency', name: 'Robux 10 000 · gift',             price: 6200,  seller: 'BlockMarket',  rating: 4.8, deals: 3210, time: '30 мин', featured: false,
    desc: '10 000 Robux через геймпасс. Комиссия платформы компенсирована. Выдача в течение 30 минут после подтверждения сделки.' },
  { id: 8,  game: 'valorant', cat: 'accounts', name: 'Аккаунт Immortal 3 · EU',         price: 11400, seller: 'RadiantShop',  rating: 4.6, deals: 410,  time: '25 мин', featured: false,
    desc: 'Аккаунт Valorant с рангом Immortal 3, регион EU. 40+ скинов, включая Reaver Vandal. Полный доступ и смена данных.' },
  { id: 9,  game: 'wot',      cat: 'currency', name: 'Золото 25 000 · RU',              price: 5100,  seller: 'TankTreasury', rating: 4.9, deals: 7650, time: '8 мин',  featured: false,
    desc: '25 000 золота на ваш аккаунт World of Tanks (Lesta RU). Зачисление подарком, аккаунт не требуется. Скидки на объёмы от 50 000.' },
  { id: 10, game: 'cs2',      cat: 'keys',     name: 'Prime Status · ключ',             price: 1290,  seller: 'KeyForge',     rating: 5.0, deals: 9840, time: '1 мин',  featured: false,
    desc: 'Ключ активации Prime Status для CS2. Моментальная выдача кода после оплаты. Регион — глобальный, активация без VPN.' },
  { id: 11, game: 'steam',    cat: 'keys',     name: 'Случайный ключ AAA',              price: 390,   seller: 'KeyForge',     rating: 4.7, deals: 12100, time: '1 мин', featured: false,
    desc: 'Случайный Steam-ключ из пула AAA-игр стоимостью от 1000 ₽. Моментальная выдача. Дубликаты в течение месяца заменяем бесплатно.' },
  { id: 12, game: 'genshin',  cat: 'topup',    name: 'Кристаллы 6480 + бонус',          price: 7900,  seller: 'PrimoStore',   rating: 4.9, deals: 4470, time: '12 мин', featured: false,
    desc: '6480 кристаллов сотворения с удвоением первой покупки. Пополнение через UID — вход в аккаунт не требуется.' },
  { id: 13, game: 'mc',       cat: 'accounts', name: 'Лицензия Java + Bedrock',         price: 2190,  seller: 'CraftKeys',    rating: 4.8, deals: 6320, time: '5 мин',  featured: false,
    desc: 'Полный доступ к аккаунту Microsoft с лицензией Minecraft Java & Bedrock. Смена почты и никнейма. Гарантия 90 дней.' },
  { id: 14, game: 'dota2',    cat: 'items',    name: 'Аркана PA · Manifold',            price: 8700,  seller: 'VeteranTrade', rating: 4.9, deals: 2140, time: '5 мин',  featured: false,
    desc: 'Manifold Paradox — аркана на Phantom Assassin. Передача обменом Steam, без ожидания. Возможен торг при покупке нескольких предметов.' },
  { id: 15, game: 'fortnite', cat: 'topup',    name: 'В-баксы 5000',                    price: 3290,  seller: 'SkinVault',    rating: 4.8, deals: 890,  time: '15 мин', featured: false,
    desc: '5000 В-баксов через подарок с личного аккаунта. Требуется 48 часов в друзьях либо покупка через свой аккаунт с полным доступом.' },
  { id: 16, game: 'valorant', cat: 'services', name: 'Буст до Diamond',                 price: 2900,  seller: 'AscendBoost',  rating: 4.9, deals: 1105, time: '2 часа', featured: false,
    desc: 'Буст ранга до Diamond от игроков Radiant. Цена за дивизион. Играем на вашем аккаунте или в дуо — на выбор.' },
];

/* ---------- helpers ---------- */

const fmtPrice = (n) => n.toLocaleString('ru-RU') + ' ₽';

function lotPlural(n) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return 'лот';
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return 'лота';
  return 'лотов';
}
const gameOf   = (id) => GAMES.find(g => g.id === id);
const catOf    = (id) => CATEGORIES.find(c => c.id === id);

/* Editorial placeholder: serif monogram in a thin ring, red accent dot */
function offerArt(offer, size = 200) {
  const g = gameOf(offer.game);
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">` +
    `<rect width="200" height="200" fill="none"/>` +
    `<circle cx="100" cy="100" r="72" fill="none" stroke="#1a1714" stroke-width="1"/>` +
    `<circle cx="100" cy="100" r="86" fill="none" stroke="#1a1714" stroke-opacity="0.18" stroke-width="1"/>` +
    `<circle cx="161" cy="61" r="6" fill="#891423"/>` +
    `<text x="100" y="100" font-family="Playfair Display, Georgia, serif" font-size="52" fill="#1a1714" text-anchor="middle" dominant-baseline="central">${g.mono}</text>` +
    `</svg>`;
  return `<img class="offer-art" width="${size}" height="${size}" alt="" loading="lazy" src="data:image/svg+xml;utf8,${encodeURIComponent(svg)}">`;
}

function offerCard(offer) {
  const g = gameOf(offer.game);
  const c = catOf(offer.cat);
  return `
    <a class="offer-card" href="product.html?id=${offer.id}">
      <span class="offer-tag">${g.name} · ${c.name}</span>
      <span class="offer-art-wrap">${offerArt(offer)}</span>
      <span class="offer-name">${offer.name}</span>
      <span class="offer-price">${fmtPrice(offer.price)}</span>
      <span class="offer-seller">${offer.seller} · ★ ${offer.rating}</span>
    </a>`;
}

/* ---------- renderers ---------- */

function renderCategories(el) {
  if (!el) return;
  el.innerHTML = CATEGORIES.map(c => `
    <a class="cat-cell" href="catalog.html?cat=${c.id}">
      <span class="cat-num">${c.num}</span>
      <span class="cat-name">${c.name}</span>
      <span class="cat-note">${c.note}</span>
      <span class="cat-count">${(n => `${n} ${lotPlural(n)}`)(OFFERS.filter(o => o.cat === c.id).length)}</span>
    </a>`).join('');
}

function renderRail(el, offers) {
  if (!el) return;
  el.innerHTML = offers.map(offerCard).join('');
}

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
