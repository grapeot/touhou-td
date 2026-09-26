# AGENTS.md

工作语言：中文。代码注释用英文。

## 结构

- `index.html`、`src/`：游戏本体，纯静态，无构建步骤。`src/core.js` 是纯逻辑（不碰 DOM），浏览器和 `scripts/sim.mjs` 共用；`src/main.js` 只做渲染、输入和音频。
- `assets/`、`audio/`：游戏实际加载的成品素材。`assets/raw/`、`assets/drafts/`、`audio/build/` 是可重建的中间产物，不进 git。
- `scripts/`：美术、音频、地图草图的生成脚本，平衡模拟器，浏览器 smoke test。
- `tests/`：`node --test`，覆盖核心逻辑和平衡护栏。
- `docs/`：`prd.md`、`rfc.md`、`test.md`、`working.md`。

## 规则

- 每次改动行为或数值，更新 `docs/working.md`（Changelog + Lessons Learned）。
- 改 `src/config.js` 的数值后必须跑 `npm test`；平衡护栏失败时先 `npm run sim` 看完整对照表，再决定是改数值还是放宽护栏。
- 游戏规则只写在 `core.js`，不要在 `main.js` 里改状态；这样模拟器看到的就是玩家玩到的。
- 地图坐标以 `scripts/make_map_draft.py` 和 `src/config.js` 为准，美术是画在坐标上的；换地图美术后要核对石台和参道是否对齐。
- 外部工具路径只从环境变量读（`.env.example`），不要把本机路径、局域网地址、API key 写进仓库。提交前扫一遍：`rg -n "/Users/|192\.168\.|op://|sk-" .`
- 默认分支 `master`，有 branch protection，所有改动走 PR。只有用户要求时才 commit。
- Python 用 uv 管理的 `.venv`（`uv pip install`）；Node 22，无 npm 依赖。
