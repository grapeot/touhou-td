// Browser shell: rendering, input, audio. All rules live in core.js.
import { MAP, TOWERS, ENEMIES, WAVES } from './config.js';
import { createGame, step, startWave, placeTower, upgradeTower, upgradeCost, sellTower, castSpell, canCast } from './core.js';

const $ = (id) => document.getElementById(id);
const canvas = $('c');
const ctx = canvas.getContext('2d');

const img = (src) => Object.assign(new Image(), { src });
const IMG = {
  map: img('assets/map.jpg'), fairy: img('assets/fairy_chibi.png'), cirno: img('assets/cirno_chibi.png'),
  reimu: img('assets/reimu_chibi.png'), marisa: img('assets/marisa_chibi.png'), sakuya: img('assets/sakuya_chibi.png'),
  portrait: { reimu: img('assets/reimu_portrait.png'), marisa: img('assets/marisa_portrait.png'), sakuya: img('assets/sakuya_portrait.png'), cirno: img('assets/cirno_portrait.png') },
};

// ---------------------------------------------------------------- audio
// SFX go through Web Audio: iOS only lets HTMLAudio start inside a tap, and these fire from the game loop.
const AC = new (window.AudioContext || window.webkitAudioContext)();
const SFX = {};
for (const k of ['spellcard', 'wave', 'boss', 'leak', 'place', 'victory', 'defeat']) {
  fetch(`audio/${k}.mp3`).then((r) => r.arrayBuffer()).then((b) => AC.decodeAudioData(b)).then((buf) => { SFX[k] = buf; });
}
const stageBgm = Object.assign(new Audio('audio/bgm.mp3?v=zun'), { loop: true, volume: 0.4 });
const bossBgm = Object.assign(new Audio('audio/boss_theme.mp3?v=zun'), { loop: true, volume: 0.45 });
let bgm = stageBgm;
function switchBgm(next) {
  if (bgm === next) return;
  bgm?.pause();
  bgm = next;
  bgm.currentTime = 0;
  bgm.muted = muted;
  bgm.play().catch(() => {});
}
let muted = false;
function play(name, vol = 0.8) {
  if (muted || !SFX[name]) return;
  const src = AC.createBufferSource();
  const gain = AC.createGain();
  gain.gain.value = vol;
  src.buffer = SFX[name];
  src.connect(gain).connect(AC.destination);
  src.start();
}

// ---------------------------------------------------------------- state
let g = createGame(Date.now() & 0xffff);
let selectedType = null, selectedTower = null, hoverPad = -1, speed = 1, running = false, paused = false;
// Build-phase countdown: the next wave starts on its own when this reaches 0.
const FIRST_WAVE_DELAY = 15, BETWEEN_WAVES_DELAY = 6;
let autoTimer = FIRST_WAVE_DELAY;
let particles = [], floaters = [], cutin = null, bossFx = 0, shake = 0;

function reset() {
  g = createGame(Date.now() & 0xffff);
  autoTimer = FIRST_WAVE_DELAY;
  setPaused(false);
  selectedType = selectedTower = null;
  particles = []; floaters = []; cutin = null;
  $('end').classList.add('hidden');
  hidePopup();
}

// ---------------------------------------------------------------- layout scaling
// Scale the fixed 1536x864 stage into the safe area (inside the iPhone notch and home
// indicator). iOS can report stale sizes right after rotation, so also re-check every frame.
let lastBox = '';
function fit() {
  const r = $('safe').getBoundingClientRect();
  const w = r.width || innerWidth, h = r.height || innerHeight;
  const s = Math.min(w / 1536, h / 864);
  const wrap = $('wrap');
  wrap.style.transformOrigin = '0 0';
  wrap.style.transform = `scale(${s})`;
  wrap.style.left = `${r.left + (w - 1536 * s) / 2}px`;
  wrap.style.top = `${r.top + (h - 864 * s) / 2}px`;
  lastBox = `${r.left},${r.top},${w},${h}`;
}
function refitIfChanged() {
  const r = $('safe').getBoundingClientRect();
  if (`${r.left},${r.top},${r.width || innerWidth},${r.height || innerHeight}` !== lastBox) fit();
}
addEventListener('resize', fit);
addEventListener('orientationchange', () => setTimeout(fit, 300));
window.visualViewport?.addEventListener('resize', fit);
fit();

function toGame(ev) {
  const r = canvas.getBoundingClientRect();
  return [(ev.clientX - r.left) / r.width * MAP.width, (ev.clientY - r.top) / r.height * MAP.height];
}
const padAt = (x, y) => MAP.pads.findIndex(([px, py]) => Math.hypot(px - x, py - y) < MAP.padRadius + 8);
const towerOnPad = (i) => g.towers.find((t) => t.pad === i);

// ---------------------------------------------------------------- input
canvas.addEventListener('mousemove', (ev) => { hoverPad = padAt(...toGame(ev)); });
canvas.addEventListener('click', (ev) => {
  const [x, y] = toGame(ev);
  const pad = padAt(x, y);
  hidePopup();
  if (pad < 0) { selectedType = null; return; }
  const t = towerOnPad(pad);
  if (t) { selectedType = null; showPopup(t); return; }
  if (selectedType && placeTower(g, pad, selectedType)) {
    if (g.gold < TOWERS[selectedType].cost) selectedType = null;
  }
});
canvas.addEventListener('contextmenu', (ev) => { ev.preventDefault(); selectedType = null; hidePopup(); });

document.querySelectorAll('.card').forEach((el) => el.addEventListener('click', () => {
  const type = el.dataset.type;
  selectedType = selectedType === type ? null : type;
  hidePopup();
}));
document.querySelectorAll('.spell').forEach((el) => el.addEventListener('click', () => castSpell(g, el.dataset.type)));
$('next').onclick = () => startWave(g);
$('pause').onclick = () => setPaused(!paused);
function setPaused(v) {
  paused = v;
  $('pause').textContent = paused ? '▶' : '⏸';
  $('pauseOverlay').classList.toggle('hidden', !paused);
  if (!running || !bgm) return;
  if (paused) bgm.pause(); else bgm.play().catch(() => {});
}
$('speed').onclick = () => { speed = speed === 1 ? 2 : speed === 2 ? 3 : 1; $('speed').textContent = `×${speed}`; };
$('mute').onclick = () => { muted = !muted; bgm.muted = muted; $('mute').textContent = muted ? '✕' : '♪'; };
$('start').onclick = () => {
  $('title').classList.add('hidden');
  running = true;
  AC.resume();
  // Touch the boss track inside this tap so iOS lets it start later from the game loop.
  bossBgm.muted = true;
  bossBgm.play().then(() => { bossBgm.pause(); bossBgm.currentTime = 0; bossBgm.muted = muted; }).catch(() => {});
  bgm.play().catch(() => {});
};
$('restart').onclick = () => { reset(); bgm.pause(); bgm = null; switchBgm(stageBgm); };
$('up').onclick = () => { if (selectedTower && upgradeTower(g, selectedTower)) showPopup(selectedTower); };
$('sell').onclick = () => { if (selectedTower) sellTower(g, selectedTower); hidePopup(); };

addEventListener('keydown', (ev) => {
  const k = ev.key.toLowerCase();
  const types = ['reimu', 'marisa', 'sakuya'];
  if ('123'.includes(k) && k) selectedType = types[+k - 1];
  else if ('qwe'.includes(k) && k) castSpell(g, types['qwe'.indexOf(k)]);
  else if (k === ' ') { ev.preventDefault(); startWave(g); }
  else if (k === 'p') setPaused(!paused);
  else if (k === 'escape') { selectedType = null; hidePopup(); }
});

function showPopup(t) {
  selectedTower = t;
  const cost = upgradeCost(t);
  $('pname').textContent = `${TOWERS[t.type].name}  Lv.${t.level + 1}`;
  $('up').textContent = cost == null ? '已满级' : `升级 ${cost}`;
  $('up').disabled = cost == null || g.gold < cost;
  $('sell').textContent = `出售 +${Math.floor(t.spent * 0.7)}`;
  const p = $('popup');
  p.style.display = 'block';
  p.style.left = `${Math.min(t.x + 50, MAP.width - 220)}px`;
  p.style.top = `${Math.max(t.y - 100, 60)}px`;
}
function hidePopup() { $('popup').style.display = 'none'; selectedTower = null; }

// ---------------------------------------------------------------- events from the core
function handleEvents() {
  for (const ev of g.events) {
    switch (ev.type) {
      case 'place': play('place', 0.6); burst(ev.tower.x, ev.tower.y, 18, 45, 60); break;
      case 'upgrade': play('place', 0.8); burst(ev.tower.x, ev.tower.y, 30, 50, 90); break;
      case 'wave': play('wave'); floaters.push({ text: `第 ${ev.wave} 波`, x: 768, y: 360, life: 1.6, size: 64 }); break;
      case 'waveClear': autoTimer = BETWEEN_WAVES_DELAY; floaters.push({ text: '击退!', x: 768, y: 360, life: 1.2, size: 56 }); break;
      case 'kill': {
        const e = ev.enemy;
        burst(e.x, e.y, ENEMIES[e.type].boss ? 120 : 14, e.type === 'swift' ? 200 : 330, ENEMIES[e.type].boss ? 260 : 150);
        floaters.push({ text: `+${ENEMIES[e.type].bounty}`, x: e.x, y: e.y - 20, life: 0.8, size: 22, color: '#ffd76a' });
        if (ENEMIES[e.type].boss) { shake = 0.6; floaters.push({ text: '⑨ 被击败了!', x: 768, y: 300, life: 2.5, size: 60 }); }
        break;
      }
      case 'leak': play('leak'); shake = 0.25; floaters.push({ text: '赛钱被抢了!', x: 330, y: 280, life: 1, size: 28, color: '#ff6a6a' }); break;
      case 'spell': play('spellcard', 0.9); cutin = { type: ev.caster, name: ev.name, t: 0 }; break;
      case 'boss':
        play('boss', 0.9);
        switchBgm(bossBgm);
        cutin = { type: 'cirno', name: '冰符「冰瀑」 · 琪露诺登场', t: 0, boss: true };
        break;
      case 'victory': play('victory'); bgm.pause(); endScreen(true); break;
      case 'defeat': play('defeat'); bgm.pause(); endScreen(false); break;
    }
  }
  g.events.length = 0;
}

function endScreen(win) {
  setTimeout(() => {
    $('endTitle').textContent = win ? '异变解决!' : '满身疮痍';
    $('endText').textContent = win
      ? `剩余残机 ${g.lives}，赛钱 ${g.gold}。今天的博丽神社依旧和平（也依旧没有香火钱）。`
      : `倒在第 ${g.wave + 1} 波。灵梦的赛钱箱空了。`;
    $('end').classList.remove('hidden');
  }, 1200);
}

function burst(x, y, n, hue, speedMax) {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2, s = 40 + Math.random() * speedMax;
    particles.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 0.5 + Math.random() * 0.5,
      hue: hue + Math.random() * 40 - 20, r: 2 + Math.random() * 4 });
  }
}

// ---------------------------------------------------------------- drawing
function drawSprite(image, x, y, h, opts = {}) {
  if (!image.complete || !image.naturalWidth) return;
  const w = h * image.naturalWidth / image.naturalHeight;
  ctx.save();
  if (opts.filter) ctx.filter = opts.filter;
  if (opts.alpha != null) ctx.globalAlpha = opts.alpha;
  ctx.translate(x, y);
  if (opts.flip) ctx.scale(-1, 1);
  ctx.drawImage(image, -w / 2, -h * 0.85, w, h);
  ctx.restore();
}

function glowDot(x, y, r, hue, core = '#fff') {
  const grd = ctx.createRadialGradient(x, y, 0, x, y, r * 2.2);
  grd.addColorStop(0, core);
  grd.addColorStop(0.35, `hsl(${hue} 100% 65%)`);
  grd.addColorStop(1, `hsla(${hue} 100% 55% / 0)`);
  ctx.fillStyle = grd;
  ctx.beginPath(); ctx.arc(x, y, r * 2.2, 0, Math.PI * 2); ctx.fill();
}

function drawBullet(b) {
  const a = Math.atan2(b.vy, b.vx);
  ctx.save();
  ctx.translate(b.x, b.y);
  if (b.kind === 'orb') {
    ctx.globalCompositeOperation = 'lighter';
    glowDot(0, 0, b.r, b.hue);
  } else if (b.kind === 'ofuda') {
    ctx.rotate(a + Math.PI / 2);
    ctx.fillStyle = '#fff'; ctx.strokeStyle = '#d8203a'; ctx.lineWidth = 2;
    ctx.fillRect(-5, -9, 10, 18); ctx.strokeRect(-5, -9, 10, 18);
    ctx.fillStyle = '#d8203a'; ctx.fillRect(-2, -5, 4, 10);
  } else if (b.kind === 'star') {
    ctx.rotate(performance.now() / 150);
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = `hsl(${b.hue} 100% 65%)`;
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
      const r = i % 2 ? b.r * 0.45 : b.r * 1.2, t = (i / 10) * Math.PI * 2;
      ctx.lineTo(Math.cos(t) * r, Math.sin(t) * r);
    }
    ctx.fill();
  } else {
    ctx.rotate(a);
    ctx.fillStyle = '#e8f0ff'; ctx.strokeStyle = '#6a7aa8'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(14, 0); ctx.lineTo(-4, -4); ctx.lineTo(-10, 0); ctx.lineTo(-4, 4); ctx.closePath();
    ctx.fill(); ctx.stroke();
  }
  ctx.restore();
}

function drawBeam(beam) {
  const t = performance.now() / 1000;
  const w = beam.width * (0.85 + 0.15 * Math.sin(t * 40)) * Math.min(1, beam.life * 2);
  ctx.save();
  ctx.translate(beam.x, beam.y);
  ctx.rotate(beam.angle);
  ctx.globalCompositeOperation = 'lighter';
  const grd = ctx.createLinearGradient(0, -w, 0, w);
  grd.addColorStop(0, 'rgba(255,80,200,0)');
  grd.addColorStop(0.25, `hsla(${(t * 400) % 360} 100% 60% / .7)`);
  grd.addColorStop(0.5, 'rgba(255,255,255,.95)');
  grd.addColorStop(0.75, `hsla(${(t * 400 + 120) % 360} 100% 60% / .7)`);
  grd.addColorStop(1, 'rgba(80,200,255,0)');
  ctx.fillStyle = grd;
  ctx.fillRect(0, -w, 2000, w * 2);
  glowDot(0, 0, w * 0.6, 50);
  ctx.restore();
}

function drawBossDanmaku(dt) {
  const boss = g.enemies.find((e) => ENEMIES[e.type].boss);
  if (!boss) return;
  bossFx -= dt;
  if (bossFx <= 0 && g.freeze <= 0) {
    bossFx = 0.9;
    const n = 20, off = Math.random() * 6.28;
    for (let i = 0; i < n; i++) {
      const a = off + (i / n) * Math.PI * 2;
      particles.push({ x: boss.x, y: boss.y - 40, vx: Math.cos(a) * 150, vy: Math.sin(a) * 150, life: 3, hue: 195, r: 6, ice: true });
    }
  }
}

function render(dt) {
  ctx.save();
  if (shake > 0) ctx.translate((Math.random() - 0.5) * 12 * shake, (Math.random() - 0.5) * 12 * shake);
  if (IMG.map.complete && IMG.map.naturalWidth) ctx.drawImage(IMG.map, 0, 0, MAP.width, MAP.height);
  else { ctx.fillStyle = '#5a7a4a'; ctx.fillRect(0, 0, MAP.width, MAP.height); }

  // Pads: highlight free pads while placing.
  if (selectedType) {
    const def = TOWERS[selectedType];
    MAP.pads.forEach(([x, y], i) => {
      if (towerOnPad(i)) return;
      ctx.strokeStyle = i === hoverPad ? '#ffd76a' : '#ffffff88';
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(x, y, MAP.padRadius + 4, 0, Math.PI * 2); ctx.stroke();
    });
    if (hoverPad >= 0 && !towerOnPad(hoverPad)) {
      const [x, y] = MAP.pads[hoverPad];
      ctx.fillStyle = '#ffffff18'; ctx.strokeStyle = '#ffffff66'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, y, def.range, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      drawSprite(IMG[selectedType], x, y, 100, { alpha: g.gold >= def.cost ? 0.6 : 0.25 });
    }
  }
  if (selectedTower) {
    const r = TOWERS[selectedTower.type].range * (1 + 0.1 * selectedTower.level);
    ctx.fillStyle = '#ffd76a18'; ctx.strokeStyle = '#ffd76a88'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(selectedTower.x, selectedTower.y, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  }

  const now = performance.now() / 1000;
  // Towers and enemies sorted by y so sprites overlap naturally.
  const actors = [
    ...g.towers.map((t) => ({ y: t.y, draw: () => {
      const bob = Math.sin(now * 3 + t.pad) * 3;
      if (t.type === 'sakuya' && g.sakuyaBoost > 0) glowDot(t.x, t.y - 30, 30, 220);
      drawSprite(IMG[t.type], t.x, t.y + 10 + bob, 104, { flip: Math.cos(t.aim) < 0 });
      ctx.fillStyle = '#ffd76a'; ctx.font = '18px serif'; ctx.textAlign = 'center';
      ctx.fillText('★'.repeat(t.level + 1), t.x, t.y + 34);
    } })),
    ...g.enemies.map((e) => ({ y: e.y, draw: () => {
      const def = ENEMIES[e.type];
      const bob = Math.sin(now * 6 + e.wobble) * 4;
      const frozen = g.freeze > 0;
      const filter = frozen ? 'grayscale(1) brightness(1.2)'
        : e.type === 'swift' ? 'hue-rotate(170deg) saturate(1.4)' : e.type === 'big' ? 'hue-rotate(-25deg) saturate(1.3)' : null;
      if (def.boss) drawSprite(IMG.cirno, e.x, e.y + bob, 150, { filter: frozen ? filter : null });
      else drawSprite(IMG.fairy, e.x, e.y + bob, 72 * (def.scale ?? 1), { filter, flip: true });
      if (e.slow > 0 && !frozen) { ctx.fillStyle = '#9fc4ff55'; ctx.beginPath(); ctx.arc(e.x, e.y - 10, def.radius, 0, 7); ctx.fill(); }
      if (!def.boss && e.hp < e.maxHp) {
        const w = 44 * (def.scale ?? 1);
        ctx.fillStyle = '#0008'; ctx.fillRect(e.x - w / 2, e.y - 60 * (def.scale ?? 1), w, 6);
        ctx.fillStyle = '#ff5a7a'; ctx.fillRect(e.x - w / 2, e.y - 60 * (def.scale ?? 1), w * e.hp / e.maxHp, 6);
      }
    } })),
  ].sort((a, b) => a.y - b.y);
  actors.forEach((a) => a.draw());

  g.beams.forEach(drawBeam);
  g.bullets.forEach(drawBullet);

  // Particles (kill bursts, boss ice danmaku).
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (const p of particles) {
    if (!(p.ice && g.freeze > 0)) { p.x += p.vx * dt; p.y += p.vy * dt; }
    p.life -= dt;
    if (p.ice) glowDot(p.x, p.y, p.r, p.hue, '#eaffff');
    else { ctx.fillStyle = `hsla(${p.hue} 100% 65% / ${Math.max(0, p.life)})`; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fill(); }
  }
  ctx.restore();
  particles = particles.filter((p) => p.life > 0);

  // Time stop: desaturated wash with a clock ring.
  if (g.freeze > 0) {
    ctx.save();
    ctx.globalCompositeOperation = 'saturation';
    ctx.fillStyle = `rgba(128,128,128,${Math.min(1, g.freeze)})`;
    ctx.fillRect(0, 0, MAP.width, MAP.height);
    ctx.restore();
    ctx.strokeStyle = '#bcd4ff'; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.arc(768, 432, 300, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * g.freeze / TOWERS.sakuya.spell.duration); ctx.stroke();
  }

  // Boss HP bar.
  const boss = g.enemies.find((e) => ENEMIES[e.type].boss);
  if (boss) {
    ctx.fillStyle = '#000a'; ctx.fillRect(468, 70, 600, 16);
    ctx.fillStyle = '#7fd4ff'; ctx.fillRect(468, 70, 600 * boss.hp / boss.maxHp, 16);
    ctx.fillStyle = '#fff'; ctx.font = '20px serif'; ctx.textAlign = 'center'; ctx.fillText('琪露诺', 768, 64);
  }

  for (const f of floaters) {
    f.life -= dt; f.y -= 30 * dt;
    ctx.globalAlpha = Math.min(1, f.life * 2);
    ctx.font = `bold ${f.size}px serif`; ctx.textAlign = 'center';
    ctx.lineWidth = 5; ctx.strokeStyle = '#2a1a22'; ctx.strokeText(f.text, f.x, f.y);
    ctx.fillStyle = f.color ?? '#fff'; ctx.fillText(f.text, f.x, f.y);
    ctx.globalAlpha = 1;
  }
  floaters = floaters.filter((f) => f.life > 0);

  if (cutin) drawCutin(realDt);
  ctx.restore();
}

// Spell card declaration: portrait slides across a dark band with the card name.
function drawCutin(dt) {
  cutin.t += dt;
  const T = 1.7, t = cutin.t;
  if (t > T) { cutin = null; return; }
  const ease = (x) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
  const slide = t < 0.35 ? ease(t / 0.35) : t > T - 0.3 ? 1 - ease((t - (T - 0.3)) / 0.3) : 1;
  const p = IMG.portrait[cutin.type];
  ctx.save();
  ctx.globalAlpha = 0.55 * slide;
  ctx.fillStyle = cutin.boss ? '#0a2a44' : '#2a0a1a';
  ctx.fillRect(0, 250, MAP.width, 300);
  ctx.globalAlpha = slide;
  if (p.complete && p.naturalWidth) {
    const h = 620, w = h * p.naturalWidth / p.naturalHeight;
    const x = MAP.width - w - 60 + (1 - slide) * 400 - (t * 30);
    ctx.drawImage(p, x, 864 - h - 40, w, h);
  }
  ctx.font = 'bold 54px serif'; ctx.textAlign = 'left';
  ctx.lineWidth = 8; ctx.strokeStyle = '#1a0a12';
  const tx = 120 - (1 - slide) * 300;
  ctx.strokeText(cutin.name, tx, 420); ctx.fillStyle = cutin.boss ? '#bfe8ff' : '#fff'; ctx.fillText(cutin.name, tx, 420);
  ctx.restore();
}

// ---------------------------------------------------------------- HUD
function updateHud() {
  $('gold').textContent = g.gold;
  $('lives').textContent = g.lives;
  $('wave').textContent = Math.min(g.wave + 1, WAVES.length);
  $('next').disabled = g.state !== 'build';
  $('next').textContent = g.state === 'build' ? `第 ${g.wave + 1} 波 ${Math.ceil(autoTimer)}s · 立即开始` : '波次进行中';
  document.querySelectorAll('.card').forEach((el) => {
    const def = TOWERS[el.dataset.type];
    el.querySelector('.cost').textContent = def.cost;
    el.classList.toggle('active', selectedType === el.dataset.type);
    el.classList.toggle('poor', g.gold < def.cost);
  });
  document.querySelectorAll('.spell').forEach((el) => {
    const type = el.dataset.type, spell = TOWERS[type].spell;
    const has = g.towers.some((t) => t.type === type);
    const frac = g.spellReady[type] / spell.cooldown;
    el.querySelector('.cd').style.setProperty('--p', `${Math.round(frac * 100)}%`);
    el.classList.toggle('ready', canCast(g, type));
    el.classList.toggle('off', !has);
    el.title = `${spell.name}（冷却 ${spell.cooldown}s）`;
  });
  if (selectedTower && !g.towers.includes(selectedTower)) hidePopup();
  else if (selectedTower) {
    const cost = upgradeCost(selectedTower);
    $('up').disabled = cost == null || g.gold < cost;
  }
}

// ---------------------------------------------------------------- loop
let last = performance.now();
let realDt = 0;
function frame(now) {
  const real = Math.min(0.05, (now - last) / 1000);
  last = now;
  realDt = real;
  // Slow motion during a spell card cut-in, for drama.
  const scale = cutin && cutin.t < 1.2 ? 0.35 : 1;
  if (running && !paused) {
    if (g.state === 'build') {
      autoTimer -= real * speed;
      if (autoTimer <= 0) startWave(g);
    }
    const sub = speed * scale;
    const n = Math.ceil(sub * real / (1 / 60));
    for (let i = 0; i < n; i++) step(g, (real * sub) / n);
    handleEvents();
  }
  shake = Math.max(0, shake - real);
  const vis = paused ? 0 : real * speed;
  drawBossDanmaku(vis);
  render(vis * scale);
  updateHud();
  refitIfChanged();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// Debug hook for automated browser checks.
window.__td = { get game() { return g; }, placeTower, startWave, castSpell, TOWERS };
