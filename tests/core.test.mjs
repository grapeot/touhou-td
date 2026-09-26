import test from 'node:test';
import assert from 'node:assert/strict';
import { MAP, START, TOWERS, WAVES } from '../src/config.js';
import { createGame, step, startWave, placeTower, upgradeTower, sellTower, castSpell, pointAt, PATH_LENGTH } from '../src/core.js';

test('path starts off-screen right and ends at the donation box', () => {
  assert.deepEqual(pointAt(0), MAP.waypoints[0]);
  assert.deepEqual(pointAt(PATH_LENGTH + 100), MAP.waypoints.at(-1));
});

test('placing a tower costs gold and a pad holds only one tower', () => {
  const g = createGame(1);
  assert.ok(placeTower(g, 0, 'reimu'));
  assert.equal(g.gold, START.gold - TOWERS.reimu.cost);
  assert.equal(placeTower(g, 0, 'marisa'), null);
});

test('cannot place without enough gold', () => {
  const g = createGame(1);
  g.gold = TOWERS.marisa.cost - 1;
  assert.equal(placeTower(g, 1, 'marisa'), null);
});

test('upgrade to max level, then sell refunds 70% of everything spent', () => {
  const g = createGame(1);
  g.gold = 10000;
  const t = placeTower(g, 2, 'sakuya');
  assert.ok(upgradeTower(g, t));
  assert.ok(upgradeTower(g, t));
  assert.equal(upgradeTower(g, t), false);
  const spent = TOWERS.sakuya.cost + TOWERS.sakuya.upgrade[0] + TOWERS.sakuya.upgrade[1];
  const before = g.gold;
  sellTower(g, t);
  assert.equal(g.gold - before, Math.floor(spent * 0.7));
  assert.equal(g.towers.length, 0);
});

test('waves only start from the build phase', () => {
  const g = createGame(1);
  assert.ok(startWave(g));
  assert.equal(startWave(g), false);
});

test('spells need a matching tower and an active wave', () => {
  const g = createGame(1);
  g.spellReady.reimu = 0;
  assert.equal(castSpell(g, 'reimu'), false);
  placeTower(g, 0, 'reimu');
  assert.equal(castSpell(g, 'reimu'), false);
  startWave(g);
  assert.ok(castSpell(g, 'reimu'));
  assert.equal(castSpell(g, 'reimu'), false, 'on cooldown');
});

test('time stop freezes enemies in place', () => {
  const g = createGame(1);
  placeTower(g, 9, 'sakuya');
  startWave(g);
  for (let i = 0; i < 120; i++) step(g, 1 / 60);
  g.spellReady.sakuya = 0;
  assert.ok(castSpell(g, 'sakuya'));
  const before = g.enemies.map((e) => e.dist);
  for (let i = 0; i < 60; i++) step(g, 1 / 60);
  assert.deepEqual(g.enemies.slice(0, before.length).map((e) => e.dist), before.slice(0, g.enemies.length));
});

test('the same seed and inputs replay identically', () => {
  const play = () => {
    const g = createGame(42);
    placeTower(g, 0, 'marisa');
    startWave(g);
    for (let i = 0; i < 1800; i++) step(g, 1 / 60);
    return [g.gold, g.lives, g.stats.dmg.marisa];
  };
  assert.deepEqual(play(), play());
});

test('ten waves are defined and the last one has the boss', () => {
  assert.equal(WAVES.length, 10);
  assert.ok(WAVES.at(-1).some(([type]) => type === 'cirno'));
});
