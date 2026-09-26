// Headless balance check: plays every wave with scripted strategies and reports
// who wins, where lives leak, and which tower carries the damage.
// Usage: node scripts/sim.mjs
import { pathToFileURL } from 'node:url';
import { MAP, TOWERS, ENEMIES } from '../src/config.js';
import { createGame, step, startWave, placeTower, upgradeTower, upgradeCost, castSpell, canCast, pointAt, PATH_LENGTH } from '../src/core.js';

// Rank pads by how much path lies within a typical tower range.
function padCoverage(range = 200) {
  return MAP.pads.map(([x, y], i) => {
    let covered = 0;
    for (let d = 0; d < PATH_LENGTH; d += 10) {
      const [px, py] = pointAt(d);
      if (Math.hypot(px - x, py - y) <= range) covered += 10;
    }
    return { i, covered };
  }).sort((a, b) => b.covered - a.covered).map((p) => p.i);
}
const PAD_ORDER = padCoverage();

export const STRATEGIES = {
  balanced: { types: ['reimu', 'sakuya', 'marisa'], spells: true },
  balanced_nospell: { types: ['reimu', 'sakuya', 'marisa'], spells: false },
  reimu_only: { types: ['reimu'], spells: true },
  marisa_only: { types: ['marisa'], spells: true },
  sakuya_only: { types: ['sakuya'], spells: true },
  lazy_two_towers: { types: ['reimu', 'marisa'], spells: true, maxTowers: 2, noUpgrade: true },
  worst_pads: { types: ['reimu', 'sakuya', 'marisa'], spells: true, reversePads: true },
  idle: { types: [], spells: false },
};

function build(g, s) {
  const pads = s.reversePads ? [...PAD_ORDER].reverse() : PAD_ORDER;
  for (;;) {
    const count = g.towers.length;
    const type = s.types[count % s.types.length];
    const free = pads.find((p) => !g.towers.some((t) => t.pad === p));
    const wantTower = type && free !== undefined && count < (s.maxTowers ?? 99);
    // Prefer a new tower while fewer than 5, then alternate toward upgrades.
    const cheapest = s.noUpgrade ? null : g.towers.filter((t) => upgradeCost(t) != null)
      .sort((a, b) => upgradeCost(a) - upgradeCost(b))[0];
    if (wantTower && (count < 5 || !cheapest || TOWERS[type].cost <= upgradeCost(cheapest)) && g.gold >= TOWERS[type].cost) {
      placeTower(g, free, type);
    } else if (cheapest && g.gold >= upgradeCost(cheapest)) {
      upgradeTower(g, cheapest);
    } else return;
  }
}

export function run(name, s) {
  const g = createGame(7);
  const dt = 1 / 60;
  while (g.state !== 'won' && g.state !== 'lost') {
    build(g, s);
    startWave(g);
    while (g.state === 'wave') {
      step(g, dt);
      if (s.spells) {
        for (const type of Object.keys(TOWERS)) {
          const boss = g.enemies.some((e) => e.type === 'cirno');
          if (canCast(g, type) && (g.enemies.length >= 8 || boss)) castSpell(g, type);
        }
      }
      if (g.t > 3600) throw new Error('stuck');
    }
  }
  const total = Object.values(g.stats.dmg).reduce((a, b) => a + b, 0) || 1;
  const share = Object.entries(g.stats.dmg).filter(([, v]) => v > 0)
    .map(([k, v]) => `${k} ${(100 * v / total).toFixed(0)}%`).join(', ');
  return {
    name, result: g.state, wave: g.wave + (g.state === 'lost' ? 1 : 0), lives: g.lives,
    leaks: g.stats.leaksByWave.map((v) => v ?? 0).join(' '), towers: g.towers.length,
    levels: g.towers.map((t) => t.type[0] + (t.level + 1)).join(' '), share,
    spell: `${(100 * g.stats.spellDmg / total).toFixed(0)}%`,
  };
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  // Optional global HP multiplier for tuning sweeps: node scripts/sim.mjs 1.2
  const hpk = Number(process.argv[2] ?? 1);
  for (const e of Object.values(ENEMIES)) e.hp = Math.round(e.hp * hpk);
  console.table(Object.entries(STRATEGIES).map(([n, s]) => run(n, s)));
}
