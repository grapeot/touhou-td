"""Regenerate all game art with GPT Image (github.com/grapeot/image-generation-skill).

Needs the `generate-image` CLI on PATH (or IMAGE_GEN_CMD) with an OpenAI key configured
there. Each image is one paid API call; run `--only map` etc. to redo a single piece.

    python scripts/make_map_draft.py        # layout draft the map art is painted over
    python scripts/generate_art.py          # -> assets/raw/*.png
    python scripts/process_assets.py        # chroma key + resize -> assets/

Outputs are nondeterministic: re-running gives new art, so inspect before replacing.
"""
import argparse
import os
import shlex
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, DRAFT = ROOT / "assets/raw", ROOT / "assets/drafts/map_draft.png"
MODEL = ["-m", "gpt-image-2.5-sunburst", "-q", "high", "-s", "1K"]

GREEN = ("Background: completely flat solid pure green #00FF00 chroma key, no shadows or gradients on "
         "the background, character fully inside frame, nothing green on the character.")
STYLE = ("Match the art style, lineart, coloring and rendering quality of the reference image exactly "
         "(polished doujin anime illustration).")
PORTRAIT = "Waist-up character portrait, dynamic pose as if declaring a spell card."
CHIBI = ("Chibi super-deformed full-body game sprite, 2-head-tall proportions, standing idle pose facing the "
         "viewer, slightly top-down 3/4 view, bold clean outline so it reads at small size, centered.")

MAP = ("Repaint this layout draft as a polished doujin-style anime game background for a Touhou Project tower "
       "defense game: the approach to the Hakurei Shrine in Gensokyo, strict top-down view. KEEP THE LAYOUT "
       "EXACTLY: the gray winding band is a stone-paved shrine path at exactly the same position and width; the "
       "pale circles are round stone tower platforms at exactly the same positions and size; the brown block "
       "top-left is the Hakurei Shrine roof (weathered wooden shrine with a donation box in front); dark green "
       "blobs are cherry and pine trees. The short red bar on the vertical stretch of path is a vermilion torii "
       "drawn in the usual overhead 3/4 game-map convention seen from the south: its black-capped top beam spans "
       "left-to-right ACROSS the path so walkers pass under it, pillars on both path edges. Grass, moss, fallen "
       "sakura petals, soft afternoon light, rich painterly detail. No characters, no text, no UI.")

REIMU = ("Polished doujin-style anime illustration, waist-up character portrait of Reimu Hakurei from Touhou "
         "Project: shrine maiden with long dark brown hair, large red hair bow with white frills, red-and-white "
         "miko outfit with detached white sleeves, yellow neck ribbon, holding a gohei and paper ofuda "
         "talismans, confident gentle smile, dynamic pose as if declaring a spell card. Clean crisp lineart, "
         "soft cel shading with painterly highlights, high detail. " + GREEN)

# name -> (aspect, prompt); everything except the map and Reimu uses Reimu as style reference.
STYLED = {
    "marisa_portrait": ("3:4", f"{STYLE} {PORTRAIT} Marisa Kirisame from Touhou Project: blonde long wavy hair with "
                        "a single side braid, big black witch hat with white bow, black vest dress with white apron, "
                        "holding a glowing octagonal Mini-Hakkero, mischievous grin, star sparkles. {GREEN}"),
    "sakuya_portrait": ("3:4", f"{STYLE} {PORTRAIT} Sakuya Izayoi from Touhou Project: silver bob hair with small "
                        "braids, white maid headband, blue and white maid outfit, holding several silver throwing "
                        "knives fanned between her fingers, cool composed expression, a pocket watch floating nearby. {GREEN}"),
    "cirno_portrait": ("3:4", f"{STYLE} {PORTRAIT} Cirno from Touhou Project: short light-blue hair with a big "
                       "dark-blue bow, six crystalline ice wings, blue dress with white blouse and red ribbon, cocky "
                       "childish grin, frosty sparkles and small ice shards around her. {GREEN}"),
    "reimu_chibi": ("1:1", f"{STYLE} {CHIBI} Reimu Hakurei (the character in the reference), holding a gohei. {GREEN}"),
    "marisa_chibi": ("1:1", f"{STYLE} {CHIBI} Marisa Kirisame from Touhou Project: blonde hair with side braid, big "
                     "black witch hat, black dress with white apron, riding-broom held in hand. {GREEN}"),
    "sakuya_chibi": ("1:1", f"{STYLE} {CHIBI} Sakuya Izayoi from Touhou Project: silver bob hair, maid headband, "
                     "blue and white maid outfit, knives in hand. {GREEN}"),
    "cirno_chibi": ("1:1", f"{STYLE} {CHIBI} Cirno from Touhou Project: light-blue hair, dark-blue bow, six ice "
                    "crystal wings, blue dress, arms crossed confidently. {GREEN}"),
    "fairy_chibi": ("1:1", f"{STYLE} {CHIBI} A generic Touhou-style fairy enemy (fodder mob): small girl with short "
                    "orange hair, simple white-and-orange dress, translucent insect-like wings, flying pose. {GREEN}"),
}


def gen(name, aspect, prompt, inputs=()):
    cmd = shlex.split(os.environ.get("IMAGE_GEN_CMD", "generate-image")) + MODEL + ["-a", aspect]
    for i in inputs:
        cmd += ["-i", str(i)]
    cmd += ["-o", str(RAW / f"{name}.png"), "-p", prompt.format(GREEN=GREEN)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    print(("ok  " if proc.returncode == 0 else "FAIL"), name, proc.stderr[-300:] if proc.returncode else "")
    return proc.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="subset of names, e.g. map reimu_portrait marisa_chibi")
    args = ap.parse_args()
    want = set(args.only or ["map", "reimu_portrait", *STYLED])
    RAW.mkdir(parents=True, exist_ok=True)
    jobs = []
    with ThreadPoolExecutor(4) as pool:
        if "map" in want:
            if not DRAFT.exists():
                sys.exit("run scripts/make_map_draft.py first")
            jobs.append(pool.submit(gen, "map", "16:9", MAP, [DRAFT]))
        if "reimu_portrait" in want:
            gen("reimu_portrait", "3:4", REIMU)  # style anchor: must exist before the rest
        ref = RAW / "reimu_portrait.png"
        for name, (aspect, prompt) in STYLED.items():
            if name in want:
                jobs.append(pool.submit(gen, name, aspect, prompt, [ref]))
    sys.exit(0 if all(j.result() for j in jobs) else 1)


if __name__ == "__main__":
    main()
