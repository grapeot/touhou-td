# Working notes

## Changelog

### 2026-09-25

- 用 PIL 画地图布局草图，GPT Image 重绘成神社参道俯视图；十个石台和参道对齐坐标。
- GPT Image 生成灵梦立绘作风格锚点，再以它为参考生成魔理沙、咲夜、琪露诺立绘和五个 Q 版 sprite，绿幕抠图。
- 写 `core.js` 纯逻辑与 `main.js` 渲染外壳：三种塔、三张符卡、十波敌人、Boss 琪露诺。
- 写无头平衡模拟器，四轮调参后锁定数值。
- 加移动端适配：禁止缩放、横屏提示；音效改走 Web Audio 以兼容 iOS。
- 鸟居从横向参道移到纵向参道，修正朝向。
- 音乐三版：26 秒循环 → 分段结构（1:49 + Boss 曲）→ 按 zun-music-skill 重写并用 NeoTHFont 渲染（1:44 + 1:09）。
- 加自动开波倒计时（首波 15 秒，之后 6 秒）和暂停，暂停时可摆塔。
- 按 project scaffold 规范整理：`tools/` 改名 `scripts/`，外部工具路径改为环境变量，新增 `tests/`、`docs/`、`AGENTS.md`、`.env.example`。
- 验证：`npm test` 14 passed；smoke test 无控制台错误；隐私扫描零匹配。
- 加 CI（`npm test` + py_compile）与 GitHub Pages 部署 workflow；右上角加 GitHub 源码图标，标题页加源码链接。
- 地图图片加载失败时不再每帧抛异常，改画纯色底；smoke 测试服务器加大连接队列，避免并发加载时 connection reset。

### 2026-09-26

- 修复手机横屏时画面边缘被刘海和圆角遮住：按 safe area 缩放居中，并在旋转后和每帧检查尺寸变化时重新适配。
- 用户反馈两侧仍看不见：缩放基准改为 safe area 与 visual viewport 的交集（页面被缩放或工具栏遮挡时 visual viewport 小于布局视口），舞台改 position: fixed；加 `?debug` 诊断浮层显示各项尺寸。

- 降低手机发热：地图改为画布下的静态 <img>；精灵按显示尺寸预缩放、敌人色调预先算好（不再逐帧 ctx.filter）；光点改用缓存的小画布（不再逐帧建径向渐变）；时停改用半透明蒙层；HUD 只在数值变化时写 DOM；触屏设备限 30 fps，暂停和标题页限 15 fps。`scripts/perf.py --mobile`（4× CPU 降速、Boss 波）主线程忙碌占比 94% → 16%。
- 暂停键改用 SVG 图标，不用 emoji。

- 自查修复：HUD 按钮统一高度（图标按钮原来比文字按钮矮）；Boss 血条移到 HUD 下方、名字写进血条；切出页面或锁屏自动暂停并停音乐；iOS 音频被打断后点屏幕恢复；手机上升级/出售弹窗、角色卡、标题页文字放大，弹窗按钮不换行；结算时清掉时停残留。新增 `scripts/audit.py` 在手机尺寸触屏视口跑完整流程。

## Lessons Learned

- 平衡要靠模拟器，不靠截图。第一版数值下只建两座塔也能撑到第七波，画面上完全看不出来。
- 模拟器里单一角色伤害占比为 0 不一定是 bug：前排塔溢出伤害时，后排塔根本摸不到敌人。
- 图像模型画鸟居默认正面视角，在横向道路上会显得和路平行。与其反复 prompt 纠正，不如把鸟居放到纵向道路上。三次修改尝试都失败后才换思路。
- GPT Image 重绘能保持布局，但每次重绘整图都会有轻微漂移（平均像素差约 5/255），石台位置目测不变。改美术后仍需核对。
- 短音效做 loudnorm 容易削波；短 cue 用较低 gain 和更低的响度目标。
- `node --test tests/` 在 Node 22 上把目录当文件，要写成 `tests/*.test.mjs`。
- 摆塔位置对胜负影响很小（`worst_pads` 和 `balanced` 差不多），因为几乎每个石台都覆盖两段参道。想让摆位成为决策，需要改地图。
- `viewport-fit=cover` 会让页面铺到 iPhone 刘海下面，固定比例的舞台必须按 `env(safe-area-inset-*)` 围出的区域缩放；iOS 旋转后 resize 事件里的尺寸可能是旧的，要补 orientationchange、visualViewport 和逐帧检查。
- 画布性能的大头不在 JS 逻辑（只占 2–5%），在绘制：逐帧 ctx.filter、逐帧 createRadialGradient、全屏大图重绘和 saturation 混合。都能预渲染成小画布复用。
- 舞台固定 1536×864 再整体缩放，手机上实际字号约为 CSS 字号的 0.45 倍；面向手机的文字和按钮在 CSS 里要按这个比例放大。
- SVG 图标按钮会比文字按钮矮，HUD 按钮要统一写死高度。
