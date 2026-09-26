"""Compose the game's MIDI sound-effect cues (music: scripts/zun_themes.py), then render them.

Specs go through score_cue.py ($SCORE_CUE_SCRIPT), which renders with
fluidsynth, trims, loudness-normalizes and measures. Final files are MP3.
A Suno track can still replace audio/bgm.mp3 or audio/boss_theme.mp3 as-is.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose_music import boss_theme, stage_theme  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import require  # noqa: E402

SCORE = require("SCORE_CUE_SCRIPT", "path to score_cue.py, the MIDI cue renderer")
SPECS, OUT = ROOT / "audio/specs", ROOT / "audio/build"

KOTO, BELLS, STRINGS, TAIKO, BRASS, LEAD, PIANO, BASS = 107, 14, 48, 116, 61, 81, 0, 38


def n(at, note, dur, vel=90):
    return {"at": round(at, 4), "note": note, "dur": round(dur, 4), "vel": vel}


def track(name, program, channel, notes, reverb=70):
    return {"name": name, "program": program, "channel": channel, "reverb": reverb, "notes": notes}


def spec(name, duration, tracks, fade_in=0.01, fade_out=None, loudnorm="I=-20:TP=-4:LRA=11", gain=3.0):
    return {
        "name": name, "duration": duration, "bpm": 60, "tracks": tracks,
        "render": {"gain": gain, "sample_rate": 48000, "fade_in": fade_in,
                   "fade_out_start": fade_out if fade_out is not None else duration - 0.25,
                   "fade_out_dur": 0.25, "loudnorm": loudnorm},
    }


def cues():
    out = []
    # Spell card declaration: fast rising arpeggio, bell shimmer, taiko hit.
    arp = [n(i * 0.05, p, 0.5, 100) for i, p in enumerate([69, 72, 76, 81, 84, 88])]
    out.append(spec("spellcard", 1.4, [
        track("arp", KOTO, 0, arp),
        track("bell", BELLS, 1, [n(0.3, 93, 1.0, 90), n(0.3, 88, 1.0, 80)], 110),
        track("hit", TAIKO, 2, [n(0.3, 45, 0.6, 127)]),
    ]))
    # Wave start: short koto phrase.
    out.append(spec("wave", 1.2, [
        track("koto", KOTO, 0, [n(0, 76, 0.3), n(0.15, 74, 0.3), n(0.3, 76, 0.3), n(0.45, 81, 0.7, 110)]),
    ]))
    # Boss entrance: low strings swell over taiko rolls.
    taiko = [n(i * 0.18, 41 if i % 2 else 45, 0.3, 80 + i * 4) for i in range(10)]
    out.append(spec("boss", 2.6, [
        track("low", STRINGS, 0, [n(0, 45, 2.5, 100), n(0, 52, 2.5, 90), n(0.9, 57, 1.6, 100)], 100),
        track("taiko", TAIKO, 1, taiko),
    ]))
    # Enemy reached the shrine: descending minor third.
    out.append(spec("leak", 0.7, [track("koto", KOTO, 0, [n(0, 72, 0.3, 100), n(0.15, 69, 0.5, 90)])]))
    # Tower placed: soft pluck.
    out.append(spec("place", 0.4, [track("koto", KOTO, 0, [n(0, 81, 0.35, 85), n(0.05, 88, 0.3, 70)])]))
    # Victory: major cadence. Defeat: falling minor line.
    out.append(spec("victory", 2.5, [
        track("brass", BRASS, 0, [n(0, 72, 0.3), n(0.3, 76, 0.3), n(0.6, 79, 0.3), n(0.9, 84, 1.5, 110)]),
        track("str", STRINGS, 1, [n(0.9, 60, 1.5), n(0.9, 64, 1.5), n(0.9, 67, 1.5)], 100),
    ]))
    out.append(spec("defeat", 2.5, [
        track("str", STRINGS, 0, [n(0, 69, 0.6), n(0.6, 67, 0.6), n(1.2, 64, 0.6), n(1.8, 57, 0.7, 70)], 110),
    ]))
    return out


def themes():
    """Looping stage and boss themes (no fades, so the loop seam stays tight)."""
    out = []
    for name, fn in (("bgm", stage_theme), ("boss_theme", boss_theme)):
        tracks, total = fn()
        out.append(spec(name, round(total, 3), tracks, fade_in=0.001, fade_out=total - 0.02,
                        loudnorm="I=-20:TP=-3:LRA=11", gain=6.0))
    return out


def main():
    SPECS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    # Music comes from scripts/zun_themes.py; themes() is the older plain-MIDI version, kept for reference.
    for s in cues():
        path = SPECS / f"{s['name']}.json"
        path.write_text(json.dumps(s, indent=1))
        r = subprocess.run([sys.executable, str(SCORE), "render", str(path), "--outdir", str(OUT)],
                           capture_output=True, text=True)
        if r.returncode:
            failed.append(s["name"])
            print(r.stdout[-800:], r.stderr[-800:])
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUT / f"{s['name']}.wav"),
                        "-b:a", "160k", str(ROOT / f"audio/{s['name']}.mp3")], check=True)
        print("ok" if r.returncode == 0 else "CHECK", s["name"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
