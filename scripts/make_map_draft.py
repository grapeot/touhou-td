"""Layout draft for the shrine-approach map.

The draft is the source of truth for geometry: path waypoints and tower pads
are written to src/map.json, and the same coordinates are drawn here so GPT
Image can repaint the art on top without owning the layout.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
W, H = 1536, 864
PATH_WIDTH = 72

# Enemies enter off the right edge and walk to the donation box at the shrine.
WAYPOINTS = [
    (1600, 700), (1260, 700), (1260, 470), (900, 470),
    (900, 730), (520, 730), (520, 330), (300, 330),
]
PADS = [
    (1390, 580), (1130, 590), (1090, 350), (760, 360), (780, 600),
    (640, 610), (700, 830), (400, 570), (640, 450), (400, 430),
]
SHRINE_BOX = (40, 60, 300, 330)
# The torii spans the path where it runs up-screen, so its front view reads as across the path.
TORII = (520, 470)


def main():
    img = Image.new("RGB", (W, H), (96, 140, 78))
    d = ImageDraw.Draw(img)

    # Scattered tree canopies away from the path and pads.
    for x, y in [(120, 520), (200, 760), (330, 690), (1450, 120), (1300, 200),
                 (1150, 110), (980, 200), (760, 160), (1480, 380), (1500, 830),
                 (80, 400), (420, 90), (600, 120)]:
        d.ellipse((x - 55, y - 55, x + 55, y + 55), fill=(52, 96, 52))

    d.line(WAYPOINTS, fill=(168, 162, 150), width=PATH_WIDTH, joint="curve")
    for x, y in WAYPOINTS:
        r = PATH_WIDTH // 2
        d.ellipse((x - r, y - r, x + r, y + r), fill=(168, 162, 150))

    d.rectangle(SHRINE_BOX, fill=(120, 80, 50), outline=(60, 40, 30), width=6)
    d.rectangle((250, 300, 320, 360), fill=(90, 60, 40))  # donation box
    tx, ty = TORII
    d.rectangle((tx - 62, ty - 8, tx + 62, ty + 8), fill=(200, 40, 30))

    for x, y in PADS:
        d.ellipse((x - 40, y - 40, x + 40, y + 40), fill=(205, 195, 170),
                  outline=(120, 110, 90), width=5)

    img.save(ROOT / "assets/drafts/map_draft.png")
    (ROOT / "src/map.json").write_text(json.dumps({
        "width": W, "height": H, "pathWidth": PATH_WIDTH,
        "waypoints": WAYPOINTS, "pads": PADS, "goal": WAYPOINTS[-1],
    }, indent=2))


if __name__ == "__main__":
    main()
