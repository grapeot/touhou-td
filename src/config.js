// Game data. Geometry comes from scripts/make_map_draft.py (the art is painted over it).
export const MAP = {
  width: 1536,
  height: 864,
  waypoints: [[1600, 700], [1260, 700], [1260, 470], [900, 470], [900, 730], [520, 730], [520, 330], [300, 330]],
  pads: [[1390, 580], [1130, 590], [1090, 350], [760, 360], [780, 600], [640, 610], [700, 830], [400, 570], [640, 450], [400, 430]],
  padRadius: 40,
};

export const START = { gold: 220, lives: 20 };

export const TOWERS = {
  reimu: {
    name: '博丽灵梦', cost: 100, range: 200, rate: 0.7, dmg: 8, speed: 430, radius: 9,
    shots: [2, 3, 4], upgrade: [90, 160], dmgMul: [1, 1.6, 2.5],
    spell: { name: '灵符「梦想封印」', cooldown: 30, first: 8, orbs: 4, orbsPerTower: 2, dmg: 70 },
  },
  marisa: {
    name: '雾雨魔理沙', cost: 120, range: 175, rate: 0.9, dmg: 5.5, speed: 380, radius: 10,
    shots: [5, 7, 9], spread: 0.5, upgrade: [100, 180], dmgMul: [1, 1.6, 2.5],
    spell: { name: '恋符「极限火花」', cooldown: 35, first: 12, duration: 2.5, width: 80, dps: 120 },
  },
  sakuya: {
    name: '十六夜咲夜', cost: 110, range: 190, rate: 0.32, dmg: 7, speed: 720, radius: 6,
    shots: [1, 2, 3], upgrade: [90, 170], dmgMul: [1, 1.6, 2.5], slowTime: 0.6, slowFactor: 0.8,
    spell: { name: '幻世「咲夜的世界」', cooldown: 40, first: 15, duration: 3.5, rateBoost: 3 },
  },
};

export const ENEMIES = {
  fairy: { hp: 60, speed: 70, bounty: 8, radius: 22, leak: 1 },
  swift: { hp: 38, speed: 125, bounty: 7, radius: 20, leak: 1, tint: '#7fd4ff' },
  big: { hp: 320, speed: 45, bounty: 22, radius: 32, leak: 2, scale: 1.45, tint: '#ffb070' },
  cirno: { hp: 3800, speed: 32, bounty: 300, radius: 44, leak: 10, boss: true },
};

// Each group: [type, count, interval seconds, start delay].
export const WAVES = [
  [['fairy', 8, 0.9, 0]],
  [['fairy', 12, 0.7, 0]],
  [['fairy', 8, 0.8, 0], ['swift', 6, 0.6, 5]],
  [['swift', 14, 0.5, 0], ['big', 2, 2.5, 4]],
  [['big', 4, 2.0, 0], ['fairy', 12, 0.5, 2]],
  [['fairy', 20, 0.4, 0], ['swift', 6, 0.5, 6]],
  [['big', 8, 1.2, 0], ['swift', 10, 0.45, 3]],
  [['fairy', 16, 0.35, 0], ['big', 6, 1.0, 2], ['swift', 10, 0.4, 6]],
  [['big', 12, 0.9, 0], ['swift', 20, 0.35, 4]],
  [['fairy', 10, 0.5, 0], ['cirno', 1, 1, 4], ['swift', 12, 0.4, 7], ['big', 6, 1.0, 10]],
];

export const HP_GROWTH = 0.42; // enemy hp multiplier per wave index
export const WAVE_BONUS = (i) => 30 + 6 * i;
export const SELL_REFUND = 0.7;
