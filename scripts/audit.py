"""Full-flow audit on a phone-sized touch viewport: title -> build -> 10 waves -> victory -> restart.

    python scripts/audit.py   (screenshots in shots/audit_*.png)

Checks HUD button heights match, boss music takes over, the end screen appears,
restart resets state, hiding the page pauses the game, and no page errors occur.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402
from smoke import SHOTS, serve  # noqa: E402


def main():
    SHOTS.mkdir(exist_ok=True)
    httpd = serve()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"
    errors, problems = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 844, "height": 390}, has_touch=True, is_mobile=True)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
        pg.goto(url)
        pg.wait_for_timeout(1200)
        pg.screenshot(path=str(SHOTS / "audit_1_title.png"))
        pg.tap("#start")

        heights = {s: round(pg.locator(s).bounding_box()["height"]) for s in ("#speed", "#mute", "#pause", "#next")}
        if len(set(heights.values())) != 1:
            problems.append(f"HUD button heights differ: {heights}")

        # Place through the real touch UI: card, then the pad (game coords -> screen).
        box = pg.locator("canvas").bounding_box()
        k = box["width"] / 1536
        for card, (x, y) in [("reimu", (640, 450)), ("marisa", (780, 600))]:
            pg.tap(f'.card[data-type="{card}"]')
            pg.touchscreen.tap(box["x"] + x * k, box["y"] + y * k)
        if pg.evaluate("() => window.__td.game.towers.length") != 2:
            problems.append("touch placement failed")

        pg.evaluate("""() => { const td = window.__td, g = td.game; g.gold += 20000;
          for (const [p, t] of [[0,'reimu'],[1,'marisa'],[2,'sakuya'],[3,'sakuya'],[4,'reimu'],[7,'marisa'],[8,'reimu'],[9,'sakuya']])
            td.placeTower(g, p, t);
          for (const t of g.towers) { t.level = 2; } }""")
        pg.tap("#speed"); pg.tap("#speed")  # x3
        pg.tap("#next")

        # Popup on a phone.
        pg.touchscreen.tap(box["x"] + 640 * k, box["y"] + 450 * k)
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(SHOTS / "audit_2_popup.png"))
        pg.touchscreen.tap(box["x"] + 1200 * k, box["y"] + 200 * k)

        # Hidden page pauses the game.
        pg.evaluate("() => { Object.defineProperty(document, 'hidden', {value: true, configurable: true}); document.dispatchEvent(new Event('visibilitychange')); }")
        if not pg.evaluate("() => window.__td.paused"):
            problems.append("hiding the page did not pause")
        pg.screenshot(path=str(SHOTS / "audit_3_paused.png"))
        pg.evaluate("() => { Object.defineProperty(document, 'hidden', {value: false, configurable: true}); }")
        pg.tap("#pause")

        saw_boss_music = False
        for _ in range(240):
            st = pg.evaluate("""() => { const td = window.__td, g = td.game;
              for (const t of ['reimu','marisa','sakuya']) if (g.spellReady[t] <= 0) td.castSpell(g, t);
              return [g.state, g.wave, td.music, g.enemies.some(e => e.type === 'cirno')]; }""")
            if st[2] == "boss":
                saw_boss_music = True
                if st[3]:
                    pg.screenshot(path=str(SHOTS / "audit_4_boss.png"))
            if st[0] in ("won", "lost"):
                break
            pg.wait_for_timeout(1000)
        if st[0] != "won":
            problems.append(f"did not win: {st}")
        if not saw_boss_music:
            problems.append("boss music never started")
        pg.wait_for_timeout(1800)
        if not pg.locator("#end").is_visible():
            problems.append("end screen not shown")
        pg.screenshot(path=str(SHOTS / "audit_5_end.png"))
        pg.tap("#restart")
        pg.wait_for_timeout(500)
        after = pg.evaluate("() => { const td = window.__td, g = td.game; return [g.state, g.wave, g.towers.length, td.music, td.paused]; }")
        if after[:3] != ["build", 0, 0] or after[3] != "stage" or after[4]:
            problems.append(f"restart state wrong: {after}")
        b.close()
    httpd.shutdown()
    print("heights", heights)
    print("problems", problems or "none")
    print("errors", errors or "none")
    return 1 if problems or errors else 0


if __name__ == "__main__":
    sys.exit(main())
