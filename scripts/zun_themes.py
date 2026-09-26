"""Stage and boss themes written with the ZUN idioms from zun-music-skill.

Original melodies (no source tune, so no skeleton check). Each theme is a chain of
16-bar sections; every section is a zun_music Arrangement placed at its own time
offset, so the skill's generators supply the trumpet-plus-piano lead with scoop and
vibrato, root/octave bass, 16th piano arpeggios, block strings and mechanical drums.
The drum fill of each section lands in the sustained last bar of the one before,
which gives ZUN's "stop, snare burst, go" transitions.

Rendered with NeoTHFont (program 56 = "Romantic Tp"), hard-trimmed to the exact
length so the files loop cleanly in the game.

    python scripts/zun_themes.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import require  # noqa: E402

SKILL = require("ZUN_MUSIC_SKILL_DIR", "checkout of github.com/grapeot/zun-music-skill")
sys.path.insert(0, str(SKILL / "src"))

from zun_music.arrange import (Arrangement, add_backing, add_bass_pickup, add_lead,  # noqa: E402
                               add_mechanical_drums, check)
from zun_music.song import DRUM_CHANNEL, Song  # noqa: E402
from zun_music.theory import pitch  # noqa: E402

SOUNDFONT = require("ZUN_MUSIC_SOUNDFONT", "path to neothfont.sf2")
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def up(bars, semis):
    """Transpose melody bars; used for ZUN's sudden whole-step key changes."""
    out = []
    for bar in bars:
        nb = []
        for name, d in bar:
            if name is None:
                nb.append((None, d))
            else:
                p = pitch(name) + semis
                nb.append((f"{NAMES[p % 12]}{p // 12 - 1}", d))
        out.append(nb)
    return out


def up_chords(bars, semis):
    return [[(NAMES[(pitch(r + "4") + semis) % 12], q, b) for r, q, b in bar] for bar in bars]


def c(root, quality="maj", beats=4):
    return [(root, quality, beats)]


# ------------------------------------------------------------------ stage theme, A minor
# Backbone bVI-bVII-i (F-G-Am); cadences on harmonic-minor E7 with F held over it (b9).
A1 = [
    [("E5", .75), ("A5", .75), ("C6", 1.5), ("B5", .25), ("C6", .25), ("B5", .25), ("A5", .25)],
    [("B5", .75), ("G5", .75), ("D6", 1.5), ("E6", .25), ("D6", .25), ("C6", .25), ("B5", .25)],
    [("C6", .75), ("B5", .25), ("A5", .5), ("E6", 2.5)],
    [("D6", .25), ("E6", .25), ("D6", .25), ("C6", .25), ("A5", 2), ("C6", .25), ("D6", .25), ("E6", .25), ("G6", .25)],
    [("C6", .75), ("A5", .75), ("F5", 1.5), ("E5", .25), ("F5", .25), ("A5", .25), ("C6", .25)],
    [("D6", .75), ("B5", .75), ("G5", 1.5), ("A5", .25), ("B5", .25), ("D6", .5)],
    [("B5", .75), ("G#5", .75), ("F5", 1.5), ("E5", .5), ("D5", .5)],
    [("C5", .5), ("E5", .5), ("A5", 2), ("B5", .25), ("C6", .25), ("D6", .25), ("E6", .25)],
]
A1_CH = [c("F"), c("G"), c("A", "min"), c("A", "min"), c("F"), c("G"), c("E", "7"), c("A", "min")]
A2 = [
    [("C6", .75), ("A5", .75), ("C6", 1), ("D6", .5), ("E6", 1)],
    [("D6", .75), ("B5", .75), ("G5", 1.5), ("A5", .25), ("B5", .25), ("C6", .25), ("D6", .25)],
    [("E6", .75), ("D6", .25), ("B5", .5), ("G5", .5), ("A5", .75), ("C6", .75), ("E6", .5)],
    [("F6", .5), ("E6", .5), ("D6", .5), ("C6", .5), ("B5", .5), ("G#5", .5), ("B5", .5), ("D6", .5)],
    [("C6", 1.5), ("B5", .25), ("C6", .25), ("A5", .75), ("F5", .75), ("A5", .5)],
    [("B5", .75), ("G5", .75), ("D6", 1.5), ("E6", .25), ("D6", .25), ("B5", .25), ("G5", .25)],
    [("A5", .75), ("F5", .25), ("A5", .5), ("D6", .5), ("F5", 1.5), ("E5", .5)],
    [("A5", 4)],
]
A2_CH = [c("F"), c("G"), [("E", "min", 2), ("A", "min", 2)], [("D", "m7", 2), ("E", "7", 2)],
         c("F"), c("G"), [("D", "m7", 2), ("E", "7", 2)], c("A", "min")]
B = [
    [("F5", .75), ("A5", .75), ("D6", 1.5), ("C6", .5), ("A5", .5)],
    [("G5", .75), ("B5", .75), ("E6", 1.5), ("D6", .5), ("B5", .5)],
    [("A5", .75), ("C6", .75), ("F6", 1.5), ("E6", .25), ("F6", .25), ("E6", .25), ("C6", .25)],
    [("D6", 2), ("B5", .25), ("C6", .25), ("D6", .25), ("E6", .25), ("G6", 1)],
    [("F6", .75), ("E6", .75), ("D6", 1.5), ("C6", .5), ("A5", .5)],
    [("G5", .75), ("B5", .75), ("E6", 1.5), ("D6", .25), ("E6", .25), ("D6", .25), ("B5", .25)],
    [("C6", .75), ("A5", .75), ("F5", .5), ("D6", .75), ("B5", .75), ("G5", .5)],
    [("G#5", 1), ("B5", 1), ("D6", 1), ("E6", .25), ("F6", .25), ("G#6", .25), ("B6", .25)],
]
B_CH = [c("D", "min"), c("E", "min"), c("F"), c("G"), c("D", "min"), c("E", "min"),
        [("F", "maj", 2), ("G", "maj", 2)], c("E", "7")]
C = [
    [("C6", .75), ("F6", .75), ("A6", 1.5), ("G6", .25), ("A6", .25), ("G6", .25), ("F6", .25)],
    [("G6", .75), ("D6", .75), ("B5", 1.5), ("C6", .25), ("D6", .25), ("E6", .25), ("F6", .25)],
    [("E6", .75), ("C6", .75), ("A5", .5), ("E6", .5), ("A6", 1.5)],
    [("G6", .25), ("A6", .25), ("G6", .25), ("E6", .25), ("C6", 1), ("D6", .5), ("E6", .5), ("G6", 1)],
    [("A6", .75), ("G6", .75), ("F6", 1), ("E6", .5), ("F6", 1)],
    [("G6", .75), ("F6", .75), ("D6", 1.5), ("E6", .25), ("F6", .25), ("G6", .25), ("A6", .25)],
    [("F6", 1), ("E6", .5), ("D6", .5), ("F6", 1.5), ("E6", .5)],
    [("A6", 4)],
]
C_CH = [c("F"), c("G"), c("A", "min"), c("A", "min"), c("F"), c("G"),
        [("D", "m7", 2), ("E", "7", 2)], c("A", "min")]

# ------------------------------------------------------------------ boss theme (Cirno), D minor
X = [
    [("D6", .75), ("F6", .75), ("Bb5", 1.5), ("C6", .25), ("D6", .25), ("F6", .5)],
    [("E6", .75), ("C6", .75), ("G5", 1.5), ("A5", .25), ("Bb5", .25), ("C6", .25), ("E6", .25)],
    [("F6", .75), ("E6", .25), ("D6", .5), ("A5", .5), ("D6", 2)],
    [("E6", .25), ("F6", .25), ("E6", .25), ("D6", .25), ("C6", .5), ("A5", .5), ("D6", .25), ("E6", .25), ("F6", .25), ("A6", .25), ("D6", 1)],
    [("F6", .75), ("D6", .75), ("Bb5", 1.5), ("A5", .25), ("Bb5", .25), ("D6", .25), ("F6", .25)],
    [("G6", .75), ("E6", .75), ("C6", 1), ("D6", .5), ("E6", 1)],
    [("D6", .5), ("Bb5", .5), ("G5", .5), ("Bb5", .5), ("Bb5", 1.5), ("A5", .5)],
    [("D6", 1.5), ("E6", .25), ("F6", .25), ("G6", .25), ("A6", .25), ("A6", 1.5)],
]
X_CH = [c("Bb"), c("C"), c("D", "min"), c("D", "min"), c("Bb"), c("C"),
        [("G", "min", 2), ("A", "7", 2)], c("D", "min")]
Y = [
    [("A6", .75), ("F6", .75), ("D6", 1.5), ("C6", .25), ("D6", .25), ("F6", .25), ("G6", .25)],
    [("G6", .75), ("E6", .75), ("C6", 1.5), ("D6", .25), ("E6", .25), ("G6", .25), ("A6", .25)],
    [("A6", .75), ("F6", .75), ("D6", .5), ("A6", .5), ("D7", 1.5)],
    [("C7", .25), ("D7", .25), ("C7", .25), ("A6", .25), ("F6", 1), ("E6", .5), ("F6", .5), ("A6", 1)],
    [("Bb6", .75), ("A6", .75), ("F6", 1), ("D6", .5), ("F6", 1)],
    [("G6", .75), ("E6", .75), ("C6", 1), ("E6", .5), ("G6", 1)],
    [("A6", .5), ("G6", .5), ("E6", .5), ("C#6", .5), ("Bb6", 1.5), ("A6", .5)],
    [("D6", 4)],
]
Y_CH = [c("Bb"), c("C"), c("D", "min"), c("D", "min"), c("Bb"), c("C"), c("A", "7"), c("D", "min")]
Z = [
    [("G5", 1.5), ("Bb5", .5), ("D6", 1), ("C6", .5), ("Bb5", .5)],
    [("A5", 1.5), ("C#6", .5), ("E6", 1), ("G6", .5), ("E6", .5)],
    [("F6", 1.5), ("E6", .25), ("F6", .25), ("D6", 2)],
    [("C6", .75), ("A5", .75), ("F5", .5), ("A5", .5), ("C6", .5), ("F6", 1)],
    [("Bb5", .75), ("D6", .75), ("G6", 1.5), ("F6", .25), ("G6", .25), ("F6", .25), ("D6", .25)],
    [("E6", .75), ("C#6", .75), ("A5", 1.5), ("Bb5", .25), ("C#6", .25), ("E6", .25), ("G6", .25)],
    [("F6", 1), ("D6", 1), ("Bb5", 1), ("D6", .5), ("F6", .5)],
    [("E6", 1), ("C#6", .5), ("A5", .5), ("A5", .25), ("C#6", .25), ("E6", .25), ("G6", .25), ("A6", 1)],
]
Z_CH = [c("G", "min"), c("A", "7"), c("D", "min"), c("F"), c("G", "min"), c("A", "7"), c("Bb"), c("A", "7")]


def section(title, bpm, parts, climax_from):
    melody = [bar for m, _ in parts for bar in m]
    chords = [bar for _, ch in parts for bar in ch]
    return Arrangement(title=title, bpm=bpm, melody=melody, chords=chords,
                       intro_bars=1, climax_from_bar=climax_from, reverb=55)


def build(sections, bpm):
    song = Song(bpm)
    t0 = 4.0  # one intro bar for the opening drum fill and bass pickup
    for i, arr in enumerate(sections):
        problems = check(arr)
        if problems:
            raise ValueError(f"{arr.title}: {problems}")
        add_lead(song, arr, t0)
        add_backing(song, arr, t0)
        add_mechanical_drums(song, arr, t0)
        if i == 0:
            add_bass_pickup(song, arr, t0)
        t0 += len(arr.melody) * 4
    for name, tr in song.tracks.items():
        tr.controls = [(91, 35 if tr.channel == DRUM_CHANNEL else 55), (93, 20)]
        if name == "Piano":
            tr.controls.append((10, 48))
        elif name == "Lead Double":
            tr.controls.append((10, 80))
    return song, t0 * 60 / bpm


def stage():
    bpm = 150
    return build([
        section("stage A", bpm, [(A1, A1_CH), (A2, A2_CH)], climax_from=8),
        section("stage B-C", bpm, [(B, B_CH), (C, C_CH)], climax_from=8),
        section("stage A-B reprise", bpm, [(A1, A1_CH), (B, B_CH)], climax_from=12),
        # Chorus, then the same chorus a whole step up: ZUN's sudden late key change.
        section("stage C modulating", bpm, [(C, C_CH), (up(C, 2), up_chords(C_CH, 2))], climax_from=0),
    ], bpm)


def boss():
    bpm = 170
    return build([
        section("boss X-Y", bpm, [(X, X_CH), (Y, Y_CH)], climax_from=8),
        section("boss Z-X", bpm, [(Z, Z_CH), (X, X_CH)], climax_from=4),
        section("boss Y modulating", bpm, [(Y, Y_CH), (up(Y, 2), up_chords(Y_CH, 2))], climax_from=0),
    ], bpm)


def render(song, seconds, name):
    out = ROOT / "audio/build"
    out.mkdir(parents=True, exist_ok=True)
    mid, wav = out / f"{name}_zun.mid", out / f"{name}_zun.wav"
    song.save(mid)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.5", "-r", "44100", "-F", str(wav), str(SOUNDFONT), str(mid)],
                   check=True, capture_output=True)
    # Hard trim to the musical length so the game's loop point is exact.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-t", f"{seconds:.3f}",
                    "-af", "loudnorm=I=-16:TP=-1.5", "-b:a", "192k", str(ROOT / f"audio/{name}.mp3")], check=True)
    return seconds


if __name__ == "__main__":
    for fn, name in ((stage, "bgm"), (boss, "boss_theme")):
        song, secs = fn()
        render(song, secs, name)
        print(f"{name}: {secs:.1f}s")
