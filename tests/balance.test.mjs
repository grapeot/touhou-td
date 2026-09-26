// Balance guard rails: scripted strategies must keep their ordering. If a tuning change
// breaks one, rerun `node scripts/sim.mjs` to see the full table before loosening a check.
import test from 'node:test';
import assert from 'node:assert/strict';
import { STRATEGIES, run } from '../scripts/sim.mjs';

const r = Object.fromEntries(Object.entries(STRATEGIES).map(([n, s]) => [n, run(n, s)]));

test('a mixed build with spells wins', () => assert.equal(r.balanced.result, 'won'));
test('doing nothing loses early', () => assert.ok(r.idle.result === 'lost' && r.idle.wave <= 2));
test('two towers without upgrades loses', () => assert.equal(r.lazy_two_towers.result, 'lost'));
test('spell cards matter: no-spell play loses', () => assert.equal(r.balanced_nospell.result, 'lost'));
test('no single character dominates the mixed build', () => {
  for (const name of ['reimu_only', 'marisa_only', 'sakuya_only']) {
    assert.ok(r[name].result === 'lost' || r[name].lives < r.balanced.lives, `${name} ${r[name].result} ${r[name].lives}`);
  }
});
