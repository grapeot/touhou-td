# 博丽神社防卫战

东方 Project 同人塔防小游戏。妖精们冲着博丽神社的赛钱箱来了，在参道两侧的石台上安排灵梦、魔理沙和咲夜守住神社，撑过十波，最后一波是琪露诺。

在线试玩：<https://grapeot.github.io/touhou-td/>（桌面浏览器或横屏手机）

## 玩法

- 点下方角色卡（或按 1/2/3）选角色，再点地图上的石台放置。
- 点已放置的角色可以升级（最高三星）或出售（返还 70%）。
- 每波清空后几秒自动开始下一波；右上角按钮可以立即开始（空格）。⏸ 暂停（P），暂停时仍可摆塔和升级。
- 波次进行中点右下角头像发动符卡（Q/W/E）：
  - 灵符「梦想封印」：一圈追踪阴阳玉。
  - 恋符「极限火花」：朝敌人方向发射粗激光。
  - 幻世「咲夜的世界」：时间停止几秒，咲夜的飞刀同时加速。
- 灵梦的符札追踪敌人，魔理沙扇形散射星弹，咲夜的飞刀射速快并附带减速。

## 本地运行

```bash
npm run serve        # 等价于 python3 -m http.server 8765
# 打开 http://localhost:8765/
```

游戏用 ES modules，必须经 HTTP 打开，直接双击 `index.html` 不行。

## 这个项目是怎么做的

这是一次分工实验：代码负责一切需要精确、有状态、可验证的部分，生成模型只负责外观。

| 层 | 谁负责 | 位置 |
|---|---|---|
| 地图几何（参道、石台坐标） | 代码画的布局草图 | `scripts/make_map_draft.py` → `src/config.js` |
| 地图美术 | GPT Image 在草图上重绘 | `scripts/generate_art.py` |
| 角色立绘与 Q 版 sprite | GPT Image，以灵梦立绘为风格锚点，绿幕抠图 | `scripts/generate_art.py`、`scripts/process_assets.py` |
| 规则、弹幕、符卡 | 代码 | `src/core.js`（纯逻辑）、`src/config.js` |
| 渲染、符卡 cut-in、粒子 | 代码 | `src/main.js` |
| 音效 | MIDI | `scripts/make_audio.py` |
| 关卡与 Boss 曲 | 按 ZUN 惯用手法写的 MIDI，NeoTHFont 渲染 | `scripts/zun_themes.py` |
| 数值平衡 | 跑同一份 core 的无头模拟器 | `scripts/sim.mjs`、`tests/balance.test.mjs` |

## 开发

```bash
npm test                 # 核心逻辑单测 + 平衡护栏
npm run sim              # 各种脚本化策略打完十波的对照表
python scripts/smoke.py  # 无头浏览器试玩并截图（需要 Playwright）
```

重新生成美术和音乐需要外部工具，路径在 `.env` 里配置（见 `.env.example`）：

- 美术：[image-generation-skill](https://github.com/grapeot/image-generation-skill) 的 `generate-image` 命令和 OpenAI API key。
- 音乐：[zun-music-skill](https://github.com/grapeot/zun-music-skill)、FluidSynth、ffmpeg 和 NeoTHFont 音色库。

## 声明

本作是[东方 Project](https://www16.big.or.jp/~zun/) 的非官方二次创作同人作品，与上海爱丽丝幻乐团无关。角色与世界观版权归 ZUN / 上海爱丽丝幻乐团所有。美术由 AI 生成，曲子为原创旋律，未使用原作曲目。

代码以 MIT 协议发布，见 `LICENSE`；该协议不涵盖东方 Project 角色本身。
