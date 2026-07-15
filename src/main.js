import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

/* ============================================================
   KRAVLER — a scroll-flight through a marketplace world.
   The camera travels a spline; page scroll = distance flown.
   Zones along the way: crystal → ember tunnel → category
   islands → game planets → vault of crates → golden gate.
============================================================ */

const canvas = document.getElementById('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.8));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x060a12, 0.03);

const camera = new THREE.PerspectiveCamera(62, innerWidth / innerHeight, 0.1, 220);

/* soft studio reflections for metals — fully procedural, no assets */
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.06).texture;

/* ---------- palette ---------- */
const GOLD    = 0xe8b34b;
const GOLD_HI = 0xffd98a;
const COPPER  = 0xc26e3d;
const EMBER   = 0xff8a3d;
const ICE     = 0x9fd0ff;
const JADE    = 0x63d6b4;
const INKROCK = 0x151b28;

const matGold   = new THREE.MeshStandardMaterial({ color: GOLD, metalness: 1, roughness: 0.22 });
const matCopper = new THREE.MeshStandardMaterial({ color: COPPER, metalness: 1, roughness: 0.32 });
const matRock   = new THREE.MeshStandardMaterial({ color: INKROCK, metalness: 0.15, roughness: 0.85, flatShading: true });

/* ---------- camera flight path ---------- */
const curve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(0, 0.6, 13),
  new THREE.Vector3(0.4, 0.3, 5),
  new THREE.Vector3(-0.8, 0.6, -6),
  new THREE.Vector3(0.9, -0.4, -18),
  new THREE.Vector3(-0.6, 0.5, -30),
  new THREE.Vector3(0, 0.2, -40),
  new THREE.Vector3(2.4, 0.9, -52),
  new THREE.Vector3(-2.6, -0.3, -64),
  new THREE.Vector3(0, 1.1, -76),
  new THREE.Vector3(1.6, -0.4, -90),
  new THREE.Vector3(-1.2, 0.7, -103),
  new THREE.Vector3(0, 0.3, -114),
  new THREE.Vector3(0, 0.5, -126),
], false, 'catmullrom', 0.4);

/* ============================================================
   ZONE 1 · the crystal (hero)
============================================================ */
const heroGroup = new THREE.Group();
heroGroup.position.set(2.6, 0.3, -2.5);
scene.add(heroGroup);

const crystal = new THREE.Mesh(
  new THREE.IcosahedronGeometry(1.7, 1),
  new THREE.MeshStandardMaterial({ color: GOLD, metalness: 1, roughness: 0.18, flatShading: true })
);
heroGroup.add(crystal);

/* bright core leaks through the facets → bloom halo */
const core = new THREE.Mesh(
  new THREE.IcosahedronGeometry(0.95, 1),
  new THREE.MeshBasicMaterial({ color: GOLD_HI })
);
heroGroup.add(core);

const heroRing = new THREE.Mesh(
  new THREE.TorusGeometry(2.9, 0.03, 12, 120),
  new THREE.MeshBasicMaterial({ color: ICE, transparent: true, opacity: 0.7 })
);
heroRing.rotation.x = Math.PI / 2.6;
heroGroup.add(heroRing);

const heroRing2 = new THREE.Mesh(
  new THREE.TorusGeometry(3.6, 0.02, 12, 120),
  new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, opacity: 0.45 })
);
heroRing2.rotation.x = Math.PI / 1.8;
heroRing2.rotation.y = 0.6;
heroGroup.add(heroRing2);

/* shards orbiting the crystal */
const shards = [];
const shardGeo = new THREE.TetrahedronGeometry(0.16, 0);
for (let i = 0; i < 26; i++) {
  const s = new THREE.Mesh(shardGeo, Math.random() < 0.6 ? matGold : matCopper);
  s.userData = {
    a: Math.random() * Math.PI * 2,
    r: 2.4 + Math.random() * 2.6,
    v: 0.1 + Math.random() * 0.25,
    y: (Math.random() - 0.5) * 2.4,
    tilt: Math.random() * Math.PI,
  };
  shards.push(s);
  heroGroup.add(s);
}
const heroLight = new THREE.PointLight(GOLD_HI, 60, 30);
heroLight.position.set(2.6, 1.5, 0.5);
scene.add(heroLight);

/* ============================================================
   ZONE 2 · ember tunnel  (z −12 … −38)
============================================================ */
const rings = [];
for (let i = 0; i < 12; i++) {
  const t = i / 11;
  const z = -5 - t * 19;
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(3.4, 0.05, 10, 80),
    new THREE.MeshBasicMaterial({
      color: i % 3 === 0 ? ICE : EMBER,
      transparent: true,
      opacity: 0.55 + 0.35 * Math.sin(t * Math.PI),
    })
  );
  /* center each ring on the flight path so we thread through it */
  const zt = findTforZ(z);
  const c = curve.getPointAt(zt);
  const ahead = curve.getPointAt(Math.min(zt + 0.02, 1));
  ring.position.copy(c);
  ring.lookAt(ahead);
  ring.userData = { spin: (Math.random() < 0.5 ? -1 : 1) * (0.15 + Math.random() * 0.3) };
  rings.push(ring);
  scene.add(ring);
}

/* dust accelerating through the tunnel */
{
  const n = 500;
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const ang = Math.random() * Math.PI * 2;
    const rad = 1.5 + Math.random() * 4;
    pos[i * 3] = Math.cos(ang) * rad;
    pos[i * 3 + 1] = Math.sin(ang) * rad * 0.7;
    pos[i * 3 + 2] = -10 - Math.random() * 32;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({
    color: EMBER, size: 0.05, transparent: true, opacity: 0.7,
    blending: THREE.AdditiveBlending, depthWrite: false,
  })));
}

/* ============================================================
   ZONE 3 · category islands  (z −46 … −66)
   floating rock + emblem, one per category
============================================================ */
const islands = [];
function island(x, y, z, buildEmblem) {
  const g = new THREE.Group();
  g.position.set(x, y, z);

  const rock = new THREE.Mesh(new THREE.DodecahedronGeometry(1.1, 0), matRock);
  rock.scale.y = 0.55;
  g.add(rock);

  const emblem = new THREE.Group();
  emblem.position.y = 1.15;
  buildEmblem(emblem);
  g.add(emblem);

  const halo = new THREE.Mesh(
    new THREE.TorusGeometry(1.5, 0.02, 8, 60),
    new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, opacity: 0.5 })
  );
  halo.rotation.x = Math.PI / 2;
  halo.position.y = 0.75;
  g.add(halo);

  const l = new THREE.PointLight(GOLD_HI, 14, 9);
  l.position.set(0, 2, 1);
  g.add(l);

  g.userData = { baseY: y, phase: Math.random() * Math.PI * 2, emblem };
  islands.push(g);
  scene.add(g);
}

/* coin stack — currency */
island(-4.2, 0.4, -31, (e) => {
  const coin = new THREE.CylinderGeometry(0.42, 0.42, 0.09, 24);
  for (let i = 0; i < 5; i++) {
    const c = new THREE.Mesh(coin, matGold);
    c.position.set((Math.random() - 0.5) * 0.12, i * 0.11, (Math.random() - 0.5) * 0.12);
    c.rotation.y = Math.random();
    e.add(c);
  }
  const top = new THREE.Mesh(coin, matGold);
  top.position.set(0.35, 0.62, 0);
  top.rotation.z = Math.PI / 2.3;
  e.add(top);
});

/* key — game keys */
island(4.6, -0.6, -35, (e) => {
  const bow = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.09, 10, 40), matCopper);
  bow.position.y = 0.45;
  e.add(bow);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.9, 10), matCopper);
  stem.position.y = -0.12;
  e.add(stem);
  const b1 = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 0.08), matCopper);
  b1.position.set(0.15, -0.42, 0);
  e.add(b1);
  const b2 = b1.clone();
  b2.position.y = -0.26;
  e.add(b2);
});

/* crystal shard — accounts */
island(-4.8, 0.8, -39, (e) => {
  const g1 = new THREE.Mesh(new THREE.OctahedronGeometry(0.5, 0), new THREE.MeshStandardMaterial({ color: ICE, metalness: 0.6, roughness: 0.15, flatShading: true }));
  g1.scale.y = 1.7;
  g1.position.y = 0.3;
  e.add(g1);
  const g1c = new THREE.Mesh(new THREE.OctahedronGeometry(0.24, 0), new THREE.MeshBasicMaterial({ color: 0xd8ecff }));
  g1c.scale.y = 1.7;
  g1c.position.y = 0.3;
  e.add(g1c);
});

/* rocket — boosting */
island(4.4, 0.9, -43, (e) => {
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.3, 0.9, 14), matGold);
  body.position.y = 0.3;
  e.add(body);
  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.42, 14), matCopper);
  nose.position.y = 0.96;
  e.add(nose);
  const flame = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.5, 10), new THREE.MeshBasicMaterial({ color: EMBER }));
  flame.rotation.x = Math.PI;
  flame.position.y = -0.4;
  e.add(flame);
  e.userData = { flame };
});

/* chest — items & skins */
island(-4, -0.7, -46, (e) => {
  const base = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.5, 0.6), matRock);
  e.add(base);
  const lid = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.28, 0.6), matCopper);
  lid.position.set(0, 0.42, -0.12);
  lid.rotation.x = -0.5;
  e.add(lid);
  const glow = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.08, 0.45), new THREE.MeshBasicMaterial({ color: GOLD_HI }));
  glow.position.y = 0.28;
  e.add(glow);
});

/* gift — top-ups */
island(4.8, -0.2, -50, (e) => {
  const box = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.7, 0.7), new THREE.MeshStandardMaterial({ color: 0x2c3550, metalness: 0.4, roughness: 0.5 }));
  e.add(box);
  const rib1 = new THREE.Mesh(new THREE.BoxGeometry(0.74, 0.74, 0.16), matGold);
  e.add(rib1);
  const rib2 = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.74, 0.74), matGold);
  e.add(rib2);
});

/* ============================================================
   ZONE 4 · game planets  (around z −78)
============================================================ */
const planetHub = new THREE.Group();
planetHub.position.set(-8, -2.5, -61);
scene.add(planetHub);

const planetDefs = [
  { c: GOLD,    r: 0.85, orbit: 4.4, ring: true },
  { c: ICE,     r: 0.6,  orbit: 5.8 },
  { c: COPPER,  r: 0.7,  orbit: 7.4, ring: true },
  { c: JADE,    r: 0.5,  orbit: 6.6 },
  { c: 0x8fa3c8, r: 0.55, orbit: 5.0 },
  { c: EMBER,   r: 0.42, orbit: 8.4 },
  { c: 0xd9c8a8, r: 0.62, orbit: 9.2, ring: true },
  { c: 0x7f6cd9, r: 0.48, orbit: 7.9 },
];
const planets = [];
planetDefs.forEach((d, i) => {
  const p = new THREE.Mesh(
    new THREE.SphereGeometry(d.r, 26, 18),
    new THREE.MeshStandardMaterial({ color: d.c, metalness: 0.55, roughness: 0.4 })
  );
  if (d.ring) {
    const rg = new THREE.Mesh(
      new THREE.TorusGeometry(d.r * 1.7, 0.025, 8, 60),
      new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, opacity: 0.6 })
    );
    rg.rotation.x = Math.PI / 2.4;
    p.add(rg);
  }
  p.userData = {
    a: (i / planetDefs.length) * Math.PI * 2,
    orbit: d.orbit * 0.8,
    v: 0.05 + Math.random() * 0.08,
    y: (Math.random() - 0.5) * 3.4,
  };
  planets.push(p);
  planetHub.add(p);
});

/* central sun of the hub */
const hubSun = new THREE.Mesh(new THREE.SphereGeometry(1.15, 30, 22), new THREE.MeshBasicMaterial({ color: GOLD_HI }));
planetHub.add(hubSun);
const hubLight = new THREE.PointLight(GOLD_HI, 50, 40);
planetHub.add(hubLight);

/* ============================================================
   ZONE 5 · the vault  (z −96 … −120) — aisles of loot crates
============================================================ */
const crates = [];
const crateGeo = new THREE.BoxGeometry(1.15, 1.15, 1.15);
const crateEdge = new THREE.EdgesGeometry(crateGeo);
for (let i = 0; i < 18; i++) {
  const side = i % 2 === 0 ? -1 : 1;
  const z = -76 - Math.floor(i / 2) * 3.2;
  const g = new THREE.Group();
  g.position.set(side * (3.4 + Math.random() * 1.6), (Math.random() - 0.5) * 3.2, z);

  const body = new THREE.Mesh(crateGeo, new THREE.MeshStandardMaterial({ color: 0x131a29, metalness: 0.5, roughness: 0.45 }));
  g.add(body);
  const edges = new THREE.LineSegments(crateEdge, new THREE.LineBasicMaterial({ color: i % 5 === 0 ? ICE : GOLD, transparent: true, opacity: 0.9 }));
  g.add(edges);
  const slit = new THREE.Mesh(
    new THREE.BoxGeometry(1.18, 0.06, 1.18),
    new THREE.MeshBasicMaterial({ color: i % 5 === 0 ? 0xd8ecff : GOLD_HI })
  );
  g.add(slit);

  g.rotation.set(Math.random() * 0.5, Math.random() * Math.PI, Math.random() * 0.5);
  g.userData = { vy: 0.2 + Math.random() * 0.4, baseY: g.position.y, phase: Math.random() * 7 };
  crates.push(g);
  scene.add(g);
}

/* ============================================================
   ZONE 5.5 · guarantee checkpoints  (z −100 … −112)
   three gold beacons echoing the three escrow steps
============================================================ */
const beacons = [];
[[-2.6, 0.9, -108], [2.6, -0.4, -113], [0, 1.2, -118]].forEach(([x, y, z], i) => {
  const g = new THREE.Group();
  g.position.set(x, y, z);
  const gem = new THREE.Mesh(new THREE.OctahedronGeometry(0.5, 0), matGold);
  g.add(gem);
  const gemCore = new THREE.Mesh(new THREE.OctahedronGeometry(0.26, 0), new THREE.MeshBasicMaterial({ color: GOLD_HI }));
  g.add(gemCore);
  const halo = new THREE.Mesh(
    new THREE.TorusGeometry(0.95, 0.02, 8, 60),
    new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, opacity: 0.55 })
  );
  halo.rotation.x = Math.PI / 2;
  g.add(halo);
  g.userData = { baseY: y, phase: i * 2.1 };
  beacons.push(g);
  scene.add(g);
});

/* ============================================================
   ZONE 6 · the golden gate  (z −140)
============================================================ */
const gate = new THREE.Group();
gate.position.set(0, 0.5, -138);
scene.add(gate);

const gateRing = new THREE.Mesh(new THREE.TorusGeometry(5, 0.22, 18, 120), matGold);
gate.add(gateRing);
const gateRing2 = new THREE.Mesh(
  new THREE.TorusGeometry(5.8, 0.05, 12, 120),
  new THREE.MeshBasicMaterial({ color: EMBER, transparent: true, opacity: 0.7 })
);
gate.add(gateRing2);
const gateDisc = new THREE.Mesh(
  new THREE.CircleGeometry(4.7, 60),
  new THREE.MeshBasicMaterial({ color: 0xffe3a8, transparent: true, opacity: 0.5 })
);
gateDisc.position.z = -0.1;
gate.add(gateDisc);
const gateLight = new THREE.PointLight(GOLD_HI, 160, 60);
gateLight.position.z = 2;
gate.add(gateLight);

/* swirl of sparks pulled into the gate */
let gateSparks;
{
  const n = 420;
  const pos = new Float32Array(n * 3);
  const seed = new Float32Array(n * 2);
  for (let i = 0; i < n; i++) {
    seed[i * 2] = Math.random() * Math.PI * 2;
    seed[i * 2 + 1] = 5.4 + Math.random() * 3.4;
    pos[i * 3 + 2] = (Math.random() - 0.5) * 6;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  gateSparks = new THREE.Points(g, new THREE.PointsMaterial({
    color: GOLD_HI, size: 0.09, transparent: true, opacity: 0.9,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  gateSparks.userData = { seed };
  gate.add(gateSparks);
}

/* ============================================================
   ambient star dust along the whole route
============================================================ */
{
  const n = 2400;
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    pos[i * 3] = (Math.random() - 0.5) * 34;
    pos[i * 3 + 1] = (Math.random() - 0.5) * 22;
    pos[i * 3 + 2] = 16 - Math.random() * 170;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({
    color: 0xaebfda, size: 0.045, transparent: true, opacity: 0.55, depthWrite: false,
  })));
}

scene.add(new THREE.AmbientLight(0x36415e, 0.9));
const travelKey = new THREE.PointLight(ICE, 30, 26); /* rides with the camera */
scene.add(travelKey);

/* ============================================================
   zone atmosphere — fog & light color drift with progress
============================================================ */
const zoneStops = [
  { t: 0.0,  fog: new THREE.Color(0x070b14), key: new THREE.Color(ICE) },
  { t: 0.17, fog: new THREE.Color(0x120a0a), key: new THREE.Color(EMBER) },
  { t: 0.36, fog: new THREE.Color(0x081210), key: new THREE.Color(JADE) },
  { t: 0.55, fog: new THREE.Color(0x0b0a16), key: new THREE.Color(0x9a8cff) },
  { t: 0.76, fog: new THREE.Color(0x120d06), key: new THREE.Color(GOLD_HI) },
  { t: 1.0,  fog: new THREE.Color(0x1a1206), key: new THREE.Color(0xfff3d8) },
];
const fogC = new THREE.Color(), keyC = new THREE.Color();
function atmosphere(t) {
  let i = 0;
  while (i < zoneStops.length - 2 && zoneStops[i + 1].t < t) i++;
  const a = zoneStops[i], b = zoneStops[i + 1];
  const k = THREE.MathUtils.clamp((t - a.t) / (b.t - a.t), 0, 1);
  fogC.lerpColors(a.fog, b.fog, k);
  keyC.lerpColors(a.key, b.key, k);
  scene.fog.color.copy(fogC);
  travelKey.color.copy(keyC);
}

/* ---------- helpers ---------- */
function findTforZ(z) {
  /* binary search along the curve for the param whose z ≈ z */
  let lo = 0, hi = 1;
  for (let i = 0; i < 24; i++) {
    const mid = (lo + hi) / 2;
    if (curve.getPointAt(mid).z > z) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

/* ============================================================
   post-processing — bloom is what sells the gold
============================================================ */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.85, 0.7, 0.32);
composer.addPass(bloom);

/* ============================================================
   flight control
============================================================ */
let target = 0, smooth = 0, mx = 0, my = 0;
const lookAhead = new THREE.Vector3();
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches || location.search.includes('instant');

addEventListener('scroll', () => {
  const max = document.documentElement.scrollHeight - innerHeight;
  target = max > 0 ? scrollY / max : 0;
}, { passive: true });

addEventListener('pointermove', (e) => {
  mx = e.clientX / innerWidth - 0.5;
  my = e.clientY / innerHeight - 0.5;
});

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
});

const clock = new THREE.Clock();
const progressBar = document.getElementById('flightbar');

function tick() {
  const t = clock.getElapsedTime();
  smooth += (target - smooth) * (reduced ? 1 : 0.055);
  const p = THREE.MathUtils.clamp(smooth, 0, 1);

  /* camera on the spline, easing toward a point slightly ahead */
  const pos = curve.getPointAt(p);
  curve.getPointAt(Math.min(p + 0.022, 1), lookAhead);
  camera.position.set(pos.x + mx * 0.9, pos.y - my * 0.6, pos.z);
  camera.lookAt(lookAhead.x + mx * 2.2, lookAhead.y - my * 1.4, lookAhead.z);

  atmosphere(p);

  /* hero */
  crystal.rotation.y = t * 0.28;
  crystal.rotation.x = Math.sin(t * 0.33) * 0.22;
  core.rotation.y = -t * 0.4;
  heroGroup.position.y = 0.3 + Math.sin(t * 0.7) * 0.18;
  heroRing.rotation.z = t * 0.25;
  heroRing2.rotation.z = -t * 0.18;
  for (const s of shards) {
    const u = s.userData;
    u.a += u.v * 0.008;
    s.position.set(Math.cos(u.a) * u.r, u.y + Math.sin(t * 0.9 + u.tilt) * 0.25, Math.sin(u.a) * u.r * 0.75);
    s.rotation.x += 0.01; s.rotation.y += 0.013;
  }

  /* tunnel */
  for (const r of rings) r.rotation.z += r.userData.spin * 0.01;

  /* islands */
  for (const g of islands) {
    const u = g.userData;
    g.position.y = u.baseY + Math.sin(t * 0.8 + u.phase) * 0.25;
    u.emblem.rotation.y = t * 0.5 + u.phase;
    if (u.emblem.userData.flame) u.emblem.userData.flame.scale.y = 0.8 + Math.sin(t * 9) * 0.25;
  }

  /* planets */
  planetHub.rotation.y = t * 0.02;
  for (const pl of planets) {
    const u = pl.userData;
    u.a += u.v * 0.008;
    pl.position.set(Math.cos(u.a) * u.orbit, u.y + Math.sin(t * 0.5 + u.orbit) * 0.35, Math.sin(u.a) * u.orbit);
    pl.rotation.y += 0.006;
  }

  /* vault */
  for (const c of crates) {
    const u = c.userData;
    c.position.y = u.baseY + Math.sin(t * u.vy + u.phase) * 0.3;
    c.rotation.y += 0.0022;
  }

  /* beacons */
  for (const b of beacons) {
    b.position.y = b.userData.baseY + Math.sin(t * 0.9 + b.userData.phase) * 0.25;
    b.rotation.y = t * 0.7 + b.userData.phase;
  }

  /* gate */
  gateRing2.rotation.z = t * 0.4;
  gateDisc.material.opacity = 0.42 + Math.sin(t * 2.2) * 0.1;
  {
    const arr = gateSparks.geometry.attributes.position.array;
    const seed = gateSparks.userData.seed;
    for (let i = 0; i < seed.length / 2; i++) {
      const a = seed[i * 2] + t * 0.35;
      const r = seed[i * 2 + 1];
      arr[i * 3] = Math.cos(a) * r;
      arr[i * 3 + 1] = Math.sin(a) * r;
    }
    gateSparks.geometry.attributes.position.needsUpdate = true;
  }

  travelKey.position.set(pos.x, pos.y + 1.4, pos.z + 1);

  if (progressBar) progressBar.style.transform = `scaleX(${p})`;

  composer.render();
  requestAnimationFrame(tick);
}
tick();
