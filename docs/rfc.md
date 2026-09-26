# RFC：架构与关键决策

## 架构

纯静态网页，无构建步骤，ES modules 直接由浏览器加载。

- `src/config.js`：全部数据（地图坐标、角色数值、敌人、波次）。
- `src/core.js`：纯逻辑。`createGame / step / startWave / placeTower / upgradeTower / sellTower / castSpell`。不碰 DOM，用 seed 固定的伪随机数，可在 Node 里确定性重放。状态变化通过 `g.events` 通知外层。
- `src/main.js`：浏览器外壳。canvas 渲染、输入、HUD、符卡 cut-in、粒子、音频、自动开波倒计时和暂停。只读 core 的状态并消费事件，不直接改规则。
- `scripts/sim.mjs`：用 core 跑脚本化策略，输出对照表；`tests/balance.test.mjs` 把关键结论变成护栏。

## 关键决策

- **规则与渲染分离。** 模拟器和玩家跑的是同一份 `core.js`，所以平衡结论直接适用于实际游戏。
- **坐标先于美术。** 地图由 `make_map_draft.py` 画出参道和石台的布局草图，再交给 GPT Image 重绘。游戏用草图坐标，美术只是皮。换美术后必须核对对齐。
- **生成模型不画动画帧。** 同一角色跨帧一致性难保证，所以每个角色只生成一张立绘和一张 Q 版图，浮动、朝向、cut-in 滑入全部由代码补间。风格一致靠同一张灵梦立绘做参考图。
- **弹幕由代码生成。** 符札、星弹、飞刀、阴阳玉、极限火花、时停都是 canvas 绘制，东方最有辨识度的视觉因此落在代码层。
- **音频分两类。** 需要对齐事件的音效用 MIDI；关卡曲和 Boss 曲按 ZUN 惯用手法（小号 + 钢琴八度叠奏、3-3-2 切分、♭VI–♭VII–i、和声小调 V7 上的 ♭9、机械鼓、突然转调）写成 MIDI，用 NeoTHFont 渲染并硬裁到精确长度以便循环。
- **iOS 音频。** 音效走 Web Audio（游戏循环里触发的 HTMLAudio 会被 iOS 拦截）；Boss 曲在点"开始"的那一下预解锁。
- **鸟居朝向。** 图像模型总把鸟居画成正面视角，所以鸟居放在纵向的一段参道上，正面视角恰好横跨参道。

## 部署

GitHub Pages，由 `.github/workflows/pages.yml` 在 `master` 更新时把静态文件打包发布。CI（`.github/workflows/ci.yml`）跑 `npm test`。
