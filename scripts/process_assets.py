"""Chroma-key the green-screen character art and build a contact sheet."""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "assets/raw", ROOT / "assets"
TARGETS = {"portrait": 900, "chibi": 256}


def key_green(img):
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # How much green dominates the other channels; soft ramp keeps edges smooth.
    excess = g - np.maximum(r, b)
    alpha = np.clip(1.0 - (excess - 40.0) / 80.0, 0.0, 1.0)
    # Despill: clamp green on semi-opaque and opaque pixels.
    a[..., 1] = np.where(excess > 0, np.maximum(r, b) + np.minimum(excess, 0), g)
    rgba = np.dstack([a, alpha * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def crop_to_content(img, pad=8):
    bbox = img.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    return img.crop((max(l - pad, 0), max(t - pad, 0),
                     min(r + pad, img.width), min(b + pad, img.height)))


def main():
    done = []
    for path in sorted(RAW.glob("*_*.png")):
        kind = path.stem.split("_")[-1]
        if kind not in TARGETS:
            continue
        img = crop_to_content(key_green(Image.open(path)))
        img.thumbnail((TARGETS[kind], TARGETS[kind]), Image.LANCZOS)
        img.save(OUT / path.name)
        done.append(img)

    Image.open(RAW / "map.png").convert("RGB").save(OUT / "map.jpg", quality=90)

    # Contact sheet on a dark checker so leftover green fringes are obvious.
    cell = 300
    sheet = Image.new("RGB", (cell * len(done), cell), (40, 30, 50))
    for i, img in enumerate(done):
        im = img.copy()
        im.thumbnail((cell - 10, cell - 10))
        sheet.paste(im, (i * cell + (cell - im.width) // 2, (cell - im.height) // 2), im)
    sheet.save(ROOT / "assets/drafts/contact_sheet.png")


if __name__ == "__main__":
    main()
