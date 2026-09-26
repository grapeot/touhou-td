// Pure game logic: no DOM, no canvas. The browser and scripts/sim.mjs both drive this.
import { MAP, START, TOWERS, ENEMIES, WAVES, HP_GROWTH, WAVE_BONUS, SELL_REFUND } from './config.js';

export function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const SEGMENTS = [];
let PATH_LENGTH = 0;
for (let i = 0; i < MAP.waypoints.length - 1; i++) {
  const [x1, y1] = MAP.waypoints[i], [x2, y2] = MAP.waypoints[i + 1];
  const len = Math.hypot(x2 - x1, y2 - y1);
  SEGMENTS.push({ x1, y1, x2, y2, len, start: PATH_LENGTH });
  PATH_LENGTH += len;
}
export { PATH_LENGTH };

export function pointAt(dist) {
  for (const s of SEGMENTS) {
    if (dist <= s.start + s.len) {
      const f = (dist - s.start) / s.len;
      return [s.x1 + (s.x2 - s.x1) * f, s.y1 + (s.y2 - s.y1) * f];
    }
  }
  const last = MAP.waypoints[MAP.waypoints.length - 1];
  return [last[0], last[1]];
}

export function createGame(seed = 1) {
  return {
    t: 0, gold: START.gold, lives: START.lives, wave: 0, state: 'build',
    spawns: [], enemies: [], towers: [], bullets: [], beams: [],
    events: [], nextId: 1, rng: mulberry32(seed),
    freeze: 0, sakuyaBoost: 0,
    spellReady: Object.fromEntries(Object.entries(TOWERS).map(([k, v]) => [k, v.spell.first])),
    stats: { dmg: { reimu: 0, marisa: 0, sakuya: 0 }, spellDmg: 0, leaksByWave: [], casts: 0 },
  };
}

const emit = (g, type, data = {}) => g.events.push({ type, t: g.t, ...data });

export function startWave(g) {
  if (g.state !== 'build' || g.wave >= WAVES.length) return false;
  const hpMul = 1 + HP_GROWTH * g.wave;
  for (const [type, count, interval, delay] of WAVES[g.wave]) {
    for (let i = 0; i < count; i++) g.spawns.push({ at: g.t + delay + i * interval, type, hpMul });
  }
  g.spawns.sort((a, b) => a.at - b.at);
  g.state = 'wave';
  g.stats.leaksByWave[g.wave] = 0;
  emit(g, 'wave', { wave: g.wave + 1 });
  return true;
}

export function placeTower(g, padIndex, type) {
  const def = TOWERS[type];
  if (!def || g.gold < def.cost || g.towers.some((t) => t.pad === padIndex)) return null;
  if (g.state === 'won' || g.state === 'lost') return null;
  const [x, y] = MAP.pads[padIndex];
  const tower = { id: g.nextId++, type, pad: padIndex, x, y, level: 0, cd: 0.2, spent: def.cost, aim: 0 };
  g.gold -= def.cost;
  g.towers.push(tower);
  emit(g, 'place', { tower });
  return tower;
}

export function upgradeCost(tower) {
  return TOWERS[tower.type].upgrade[tower.level] ?? null;
}

export function upgradeTower(g, tower) {
  const cost = upgradeCost(tower);
  if (cost == null || g.gold < cost) return false;
  g.gold -= cost; tower.spent += cost; tower.level++;
  emit(g, 'upgrade', { tower });
  return true;
}

export function sellTower(g, tower) {
  g.gold += Math.floor(tower.spent * SELL_REFUND);
  g.towers = g.towers.filter((t) => t !== tower);
  emit(g, 'sell', { tower });
}

export function canCast(g, type) {
  return g.state === 'wave' && g.spellReady[type] <= 0 && g.towers.some((t) => t.type === type);
}

export function castSpell(g, type) {
  if (!canCast(g, type)) return false;
  const spell = TOWERS[type].spell;
  const own = g.towers.filter((t) => t.type === type);
  g.spellReady[type] = spell.cooldown;
  g.stats.casts++;
  if (type === 'reimu') {
    // One volley from the strongest Reimu; more Reimus add orbs, not whole volleys.
    const t = own.reduce((a, b) => (b.level > a.level ? b : a));
    const count = spell.orbs + spell.orbsPerTower * own.length;
    {
      for (let i = 0; i < count; i++) {
        const a = (i / count) * Math.PI * 2;
        g.bullets.push({ x: t.x, y: t.y, vx: Math.cos(a) * 260, vy: Math.sin(a) * 260, speed: 330, r: 22,
          dmg: spell.dmg * TOWERS.reimu.dmgMul[t.level], owner: 'reimu', kind: 'orb', homing: true, target: null,
          life: 5, pierce: 2, hit: new Set(), spell: true, hue: (i * 360 / count) % 360 });
      }
    }
  } else if (type === 'marisa') {
    for (const t of own) {
      const target = pickTarget(g, t, 3) ?? g.enemies[0];
      const angle = target ? Math.atan2(target.y - t.y, target.x - t.x) : Math.PI;
      g.beams.push({ x: t.x, y: t.y, angle, life: spell.duration, width: spell.width,
        dps: spell.dps * TOWERS.marisa.dmgMul[t.level] });
    }
  } else if (type === 'sakuya') {
    g.freeze = spell.duration;
    g.sakuyaBoost = spell.duration;
  }
  emit(g, 'spell', { caster: type, name: spell.name });
  return true;
}

function pickTarget(g, tower, rangeMul = 1) {
  const range = TOWERS[tower.type].range * (1 + 0.1 * tower.level) * rangeMul;
  let best = null;
  for (const e of g.enemies) {
    if (Math.hypot(e.x - tower.x, e.y - tower.y) <= range && (!best || e.dist > best.dist)) best = e;
  }
  return best;
}

function damage(g, e, amount, owner, spell) {
  if (e.hp <= 0) return;
  const dealt = Math.min(amount, e.hp);
  e.hp -= amount;
  g.stats.dmg[owner] += dealt;
  if (spell) g.stats.spellDmg += dealt;
  if (e.hp <= 0) {
    g.gold += ENEMIES[e.type].bounty;
    emit(g, 'kill', { enemy: e });
  }
}

function fire(g, t) {
  const def = TOWERS[t.type];
  const target = pickTarget(g, t);
  if (!target) return false;
  const dmg = def.dmg * def.dmgMul[t.level];
  const n = def.shots[t.level];
  const base = Math.atan2(target.y - t.y, target.x - t.x);
  t.aim = base;
  for (let i = 0; i < n; i++) {
    let a = base;
    if (t.type === 'marisa') a += (i / (n - 1) - 0.5) * def.spread;
    else if (t.type === 'reimu') a += (i - (n - 1) / 2) * 0.35;
    else a += (i - (n - 1) / 2) * 0.08;
    g.bullets.push({ x: t.x, y: t.y, vx: Math.cos(a) * def.speed, vy: Math.sin(a) * def.speed,
      speed: def.speed, r: def.radius, dmg, owner: t.type,
      kind: t.type === 'reimu' ? 'ofuda' : t.type === 'marisa' ? 'star' : 'knife',
      homing: t.type === 'reimu', target, life: 1.6, pierce: 1, slow: t.type === 'sakuya', hit: new Set(), hue: (g.t * 200 + i * 40) % 360 });
  }
  return true;
}

export function step(g, dt) {
  if (g.state === 'won' || g.state === 'lost') return;
  g.t += dt;
  for (const k in g.spellReady) g.spellReady[k] = Math.max(0, g.spellReady[k] - (g.state === 'wave' ? dt : 0));
  g.freeze = Math.max(0, g.freeze - dt);
  g.sakuyaBoost = Math.max(0, g.sakuyaBoost - dt);

  while (g.spawns.length && g.spawns[0].at <= g.t) {
    const s = g.spawns.shift();
    const def = ENEMIES[s.type];
    const hp = Math.round(def.hp * s.hpMul);
    const e = { id: g.nextId++, type: s.type, hp, maxHp: hp, dist: 0, x: 0, y: 0, wobble: g.rng() * 6.28 };
    [e.x, e.y] = pointAt(0);
    g.enemies.push(e);
    if (def.boss) emit(g, 'boss', { enemy: e });
  }

  for (const e of g.enemies) {
    e.slow = Math.max(0, (e.slow ?? 0) - dt);
    if (g.freeze <= 0) e.dist += ENEMIES[e.type].speed * dt * (e.slow > 0 ? TOWERS.sakuya.slowFactor : 1);
    [e.x, e.y] = pointAt(e.dist);
    if (e.dist >= PATH_LENGTH && e.hp > 0) {
      e.hp = 0; e.leaked = true;
      const leak = ENEMIES[e.type].leak;
      g.lives -= leak;
      g.stats.leaksByWave[g.wave] += leak;
      emit(g, 'leak', { enemy: e });
    }
  }

  for (const t of g.towers) {
    const boost = t.type === 'sakuya' && g.sakuyaBoost > 0 ? TOWERS.sakuya.spell.rateBoost : 1;
    t.cd -= dt * boost;
    if (t.cd <= 0 && fire(g, t)) t.cd += TOWERS[t.type].rate;
    if (t.cd < 0) t.cd = 0;
  }

  for (const b of g.bullets) {
    b.life -= dt;
    if (b.homing) {
      if (!b.target || b.target.hp <= 0) {
        let best = null, bd = 1e9;
        for (const e of g.enemies) {
          const d = Math.hypot(e.x - b.x, e.y - b.y);
          if (e.hp > 0 && !b.hit.has(e.id) && d < bd) { bd = d; best = e; }
        }
        b.target = best;
      }
      if (b.target) {
        const want = Math.atan2(b.target.y - b.y, b.target.x - b.x);
        const cur = Math.atan2(b.vy, b.vx);
        let diff = ((want - cur + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
        const turn = Math.max(-6 * dt, Math.min(6 * dt, diff));
        b.vx = Math.cos(cur + turn) * b.speed;
        b.vy = Math.sin(cur + turn) * b.speed;
      }
    }
    b.x += b.vx * dt; b.y += b.vy * dt;
    for (const e of g.enemies) {
      if (e.hp <= 0 || b.hit.has(e.id)) continue;
      if (Math.hypot(e.x - b.x, e.y - b.y) < ENEMIES[e.type].radius + b.r) {
        b.hit.add(e.id);
        damage(g, e, b.dmg, b.owner, b.spell);
        if (b.slow) e.slow = TOWERS.sakuya.slowTime;
        if (--b.pierce <= 0) { b.life = 0; break; }
      }
    }
  }
  g.bullets = g.bullets.filter((b) => b.life > 0 && b.x > -50 && b.x < MAP.width + 50 && b.y > -50 && b.y < MAP.height + 50);

  for (const beam of g.beams) {
    beam.life -= dt;
    const cx = Math.cos(beam.angle), cy = Math.sin(beam.angle);
    for (const e of g.enemies) {
      const dx = e.x - beam.x, dy = e.y - beam.y;
      const along = dx * cx + dy * cy, across = Math.abs(-dx * cy + dy * cx);
      if (along > 0 && across < beam.width / 2 + ENEMIES[e.type].radius) damage(g, e, beam.dps * dt, 'marisa', true);
    }
  }
  g.beams = g.beams.filter((b) => b.life > 0);
  g.enemies = g.enemies.filter((e) => e.hp > 0);

  if (g.lives <= 0) { g.lives = 0; g.state = 'lost'; emit(g, 'defeat'); return; }
  if (g.state === 'wave' && !g.spawns.length && !g.enemies.length) {
    g.gold += WAVE_BONUS(g.wave);
    g.wave++;
    if (g.wave >= WAVES.length) { g.state = 'won'; emit(g, 'victory'); }
    else { g.state = 'build'; emit(g, 'waveClear', { wave: g.wave }); }
  }
}
