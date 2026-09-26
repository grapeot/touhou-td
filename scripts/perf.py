"""Rough mobile-cost benchmark: CPU-throttled Chromium, a busy boss wave, main-thread busy share.

    python scripts/perf.py [--throttle 4] [--seconds 10]

Reports main-thread task/script/layout/style time as a fraction of wall time and the frame
rate the page actually achieved. Higher busy share means more heat on a phone. This measures
CPU work only; GPU compositing cost is not captured.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402
from smoke import serve  # noqa: E402

SETUP = """() => { const td = window.__td, g = td.game; g.gold = 99999;
  [[0,'reimu'],[1,'marisa'],[2,'sakuya'],[3,'reimu'],[4,'marisa'],[5,'sakuya'],[7,'reimu'],[8,'marisa'],[9,'sakuya']]
    .forEach(([p, t]) => td.placeTower(g, p, t));
  g.wave = 9; td.startWave(g); }"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--throttle", type=float, default=4)
    ap.add_argument("--seconds", type=float, default=10)
    ap.add_argument("--viewport", default="844x390")
    ap.add_argument("--mobile", action="store_true", help="emulate a touch phone (enables the 30 fps cap)")
    args = ap.parse_args()
    w, h = map(int, args.viewport.split("x"))
    httpd = serve()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, has_touch=args.mobile, is_mobile=args.mobile)
        cdp = pg.context.new_cdp_session(pg)
        cdp.send("Performance.enable")
        pg.goto(url)
        pg.wait_for_timeout(1000)
        pg.click("#start", force=True)
        pg.evaluate(SETUP)
        pg.wait_for_timeout(6000)  # let the boss wave fill the screen
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": args.throttle})
        pg.evaluate("() => { window.__frames = 0; const f = () => { window.__frames++; requestAnimationFrame(f); }; requestAnimationFrame(f); }")
        m0 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
        pg.wait_for_timeout(int(args.seconds * 1000))
        m1 = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
        frames = pg.evaluate("() => window.__frames")
        state = pg.evaluate("() => { const g = window.__td.game; return [g.enemies.length, g.bullets.length]; }")
        b.close()
    httpd.shutdown()
    wall = args.seconds
    for k in ("TaskDuration", "ScriptDuration", "LayoutDuration", "RecalcStyleDuration"):
        print(f"{k:20s} {100 * (m1[k] - m0[k]) / wall:5.1f}% of wall")
    print(f"fps {frames / wall:.1f}  (enemies, bullets at end: {state})")


if __name__ == "__main__":
    main()
