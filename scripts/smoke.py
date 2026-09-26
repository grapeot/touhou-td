"""Browser smoke test: serve the game, script a short playthrough, save screenshots.

Usage: python scripts/smoke.py  (writes to shots/)
"""

import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "shots"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(Quiet, directory=str(ROOT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    SHOTS.mkdir(exist_ok=True)
    httpd = serve()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1536, "height": 864})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.goto(url)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(SHOTS / "01_title.png"))
        page.click("#start")

        # Place via the real UI: pick a card, click a pad on the canvas.
        page.click('.card[data-type="reimu"]')
        page.mouse.move(640, 450)
        page.wait_for_timeout(200)
        page.screenshot(path=str(SHOTS / "02_placing.png"))
        page.mouse.click(640, 450)
        page.click('.card[data-type="marisa"]')
        page.mouse.click(780, 600)
        page.evaluate("""() => { const td = window.__td; td.game.gold += 2000;
            td.placeTower(td.game, 3, "sakuya"); td.placeTower(td.game, 1, 'reimu');
            td.placeTower(td.game, 2, 'marisa'); td.placeTower(td.game, 7, 'sakuya'); }""")
        page.keyboard.press("Space")
        page.wait_for_timeout(9000)
        page.screenshot(path=str(SHOTS / "03_wave.png"))
        page.keyboard.press("q")
        page.wait_for_timeout(500)
        page.screenshot(path=str(SHOTS / "04_cutin.png"))
        page.wait_for_timeout(1600)
        page.screenshot(path=str(SHOTS / "05_orbs.png"))
        page.evaluate("() => { const g = window.__td.game; g.spellReady.marisa = 0; }")
        page.keyboard.press("w")
        page.wait_for_timeout(1900)
        page.screenshot(path=str(SHOTS / "06_spark.png"))
        # Jump to the boss wave.
        page.evaluate("""() => { const g = window.__td.game; g.enemies = []; g.spawns = []; g.bullets = [];
            g.state = 'build'; g.wave = 9; g.spellReady.sakuya = 0; }""")
        page.keyboard.press("Space")
        page.wait_for_timeout(9000)
        page.screenshot(path=str(SHOTS / "07_boss.png"))
        page.keyboard.press("e")
        page.wait_for_timeout(2200)
        page.screenshot(path=str(SHOTS / "08_timestop.png"))
        state = page.evaluate("() => { const g = window.__td.game; return {state: g.state, wave: g.wave, lives: g.lives, enemies: g.enemies.length, towers: g.towers.length}; }")
        browser.close()
    httpd.shutdown()
    print("state", state)
    print("errors", errors or "none")


if __name__ == "__main__":
    main()
