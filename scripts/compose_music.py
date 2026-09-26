"""Section-based composer for the two looping themes.

Each song is a list of sections. A section names a chord per bar, an optional
8-bar melody (eighth notes, None ties the previous note), which instrument
carries the lead, and how dense the drums are. Output is a score_cue spec.
"""

# Chord name -> (bass root, triad), all in a comfortable mid register.
CHORDS = {
    'Am': (57, [57, 60, 64]), 'F': (53, [53, 57, 60]), 'G': (55, [55, 59, 62]),
    'Em': (52, [52, 55, 59]), 'E': (52, [52, 56, 59]), 'C': (48, [48, 52, 55]),
    'Dm': (50, [50, 53, 57]), 'Bb': (46, [46, 50, 53]), 'A': (45, [45, 49, 52]),
    'Gm': (55, [55, 58, 62]),
}

# Stage theme (A minor). M1 is the original loop's melody.
M1 = [
    [69, 72, 76, 81, 79, 76, 74, 76], [77, 76, 74, 72, 74, 72, 69, 72],
    [74, 71, 67, 71, 74, 79, 77, 74], [76, None, None, 74, 72, 71, None, None],
    [81, 79, 76, 79, 81, 84, 83, 81], [77, 81, 84, 81, 77, 76, 74, 72],
    [74, 76, 77, 79, 81, 79, 77, 74], [80, None, 76, None, 71, None, 68, None],
]
M1_CHORDS = ['Am', 'F', 'G', 'Em', 'Am', 'F', 'G', 'E']
M2 = [
    [72, None, 74, 76, 77, None, 76, 74], [72, None, 67, None, 72, 74, 76, None],
    [74, None, 71, 74, 79, None, 77, 76], [76, None, None, None, 72, 74, 76, 77],
    [77, None, 76, 74, 74, None, 72, 74], [76, None, 74, 72, 71, None, 67, 71],
    [72, None, 74, None, 76, None, 77, None], [76, None, None, None, 80, None, 83, None],
]
M2_CHORDS = ['F', 'C', 'G', 'Am', 'Dm', 'Em', 'F', 'E']
M3 = [
    [81, None, 79, 81, 84, None, 81, 79], [79, None, 76, 79, 83, None, 79, 76],
    [76, 79, 83, None, 81, 79, 76, None], [81, None, None, None, 76, 79, 81, 83],
    [84, None, 83, 81, 84, None, 88, None], [86, None, 84, 83, 79, None, 83, None],
    [83, None, 80, 83, 88, None, 86, 83], [81, None, None, None, None, None, None, None],
]
M3_CHORDS = ['F', 'G', 'Em', 'Am', 'F', 'G', 'E', 'Am']

# Boss theme (D minor), faster and brighter: square lead doubled by glockenspiel.
M4 = [
    [74, 77, 81, 77, 74, None, 72, 74], [77, None, 74, 70, 74, None, 77, 79],
    [76, None, 72, 76, 79, None, 77, 76], [73, None, 76, None, 81, None, None, None],
    [86, 84, 81, None, 77, 79, 81, None], [82, None, 81, 79, 77, None, 74, None],
    [79, None, 77, 74, 70, 74, 77, 79], [81, None, None, None, 73, None, 76, None],
]
M4_CHORDS = ['Dm', 'Bb', 'C', 'A', 'Dm', 'Bb', 'Gm', 'A']
M5 = [
    [77, None, 79, None, 81, None, 82, 81], [79, None, 76, None, 72, None, 76, 79],
    [81, None, 77, 81, 86, None, 84, 81], [81, None, None, None, 74, 77, 81, 84],
    [86, None, 84, 82, 81, None, 82, 84], [84, None, 79, 76, 84, None, 88, None],
    [85, None, 81, 76, 85, None, 88, None], [81, None, None, None, None, None, 73, 76],
]
M5_CHORDS = ['Bb', 'C', 'Dm', 'Dm', 'Bb', 'C', 'A', 'A']

# Lead voices: name -> (General MIDI program, channel, reverb).
VOICES = {
    'saw': (81, 0, 60), 'trumpet': (56, 3, 70), 'flute': (73, 4, 90), 'koto': (107, 5, 80),
    'square': (80, 6, 50), 'glock': (9, 7, 90),
}


def n(at, note, dur, vel):
    return {"at": round(at, 4), "note": note, "dur": round(dur, 4), "vel": vel}


def render_song(sections, bpm):
    beat = 60 / bpm
    bar = 4 * beat
    parts = {k: [] for k in ['piano', 'bass', 'pad', 'drums', *VOICES]}
    t = 0.0
    for sec in sections:
        chords, melody = sec['chords'], sec.get('melody')
        shift = sec.get('transpose', 0)
        for b, name in enumerate(chords):
            t0 = t + b * bar
            root, triad = CHORDS[name]
            root, triad = root + shift, [p + shift for p in triad]
            style = sec.get('piano', 'block')
            if style == 'arp':
                seq = triad + [triad[0] + 12, triad[2] + 12, triad[1] + 12, triad[0] + 12, triad[2]]
                for k in range(8):
                    parts['piano'].append(n(t0 + k * beat / 2, seq[k % len(seq)] + 12, beat * 0.9, 58))
            elif style == 'block':
                for k in range(4):
                    for p in triad:
                        parts['piano'].append(n(t0 + k * beat, p + 12, beat * 0.85, 50))
            elif style == 'sparse':
                for p in triad:
                    parts['piano'].append(n(t0, p + 12, bar * 0.95, 48))
            if sec.get('bass', True):
                pattern = sec.get('bass_pattern', 'octave')
                for k in range(8):
                    if pattern == 'sync' and k in (1, 5):
                        continue
                    note = root - 12 + (12 if pattern == 'octave' and k % 2 else 0)
                    parts['bass'].append(n(t0 + k * beat / 2, note, beat / 2 * 0.85, 92))
            if sec.get('pad'):
                for p in triad:
                    parts['pad'].append(n(t0, p, bar * 0.98, 42))
            drums = sec.get('drums', 'none')
            if drums != 'none':
                for k in range(4):
                    parts['drums'].append(n(t0 + k * beat, 36 if k % 2 == 0 else 38, 0.1, 100))
                if drums == 'drive':
                    for k in (1, 3, 5, 7):
                        parts['drums'].append(n(t0 + k * beat / 2, 36, 0.1, 80))
                for k in range(8):
                    parts['drums'].append(n(t0 + k * beat / 2, 42, 0.05, 55 + 10 * (k % 2 == 0)))
                if b == 0:
                    parts['drums'].append(n(t0, 49, 1.0, 95))
                if b == len(chords) - 1 and sec.get('fill'):
                    for k in range(4):
                        parts['drums'].append(n(t0 + 2 * beat + k * beat / 2, 45 + 2 * (3 - k), 0.1, 90 + k * 8))
            if melody:
                line = melody[b % len(melody)]
                up = sec.get('octave', 0) * 12 + shift
                for i, p in enumerate(line):
                    if p is None:
                        continue
                    length = 1
                    while i + length < 8 and line[i + length] is None:
                        length += 1
                    for voice in sec['lead']:
                        v = 92 if voice != 'glock' else 70
                        extra = 12 if voice == 'glock' else 0
                        parts[voice].append(n(t0 + i * beat / 2, p + up + extra, length * beat / 2 * 0.95, v))
        t += len(chords) * bar
    tracks = []
    fixed = {'piano': (0, 1, 60), 'bass': (38, 2, 30), 'pad': (48, 8, 100), 'drums': (0, 9, 40)}
    for name, notes in parts.items():
        if not notes:
            continue
        program, channel, reverb = fixed.get(name) or VOICES[name]
        tracks.append({"name": name, "program": program, "channel": channel, "reverb": reverb, "notes": notes})
    return tracks, t


def stage_theme():
    progression = ['Am', 'F', 'G', 'E']
    sections = [
        {'chords': progression, 'piano': 'arp', 'bass': False, 'pad': True},
        {'chords': M1_CHORDS, 'melody': M1, 'lead': ['saw'], 'drums': 'basic'},
        {'chords': M1_CHORDS, 'melody': M1, 'lead': ['trumpet'], 'octave': 0, 'drums': 'basic', 'pad': True, 'fill': True},
        {'chords': M2_CHORDS, 'melody': M2, 'lead': ['flute'], 'piano': 'arp', 'bass_pattern': 'sync', 'drums': 'basic', 'pad': True},
        {'chords': M3_CHORDS, 'melody': M3, 'lead': ['saw', 'trumpet'], 'drums': 'drive', 'pad': True, 'fill': True},
        {'chords': progression, 'melody': M1[:4], 'lead': ['koto'], 'piano': 'sparse', 'bass': False},
        {'chords': M1_CHORDS, 'melody': M1, 'lead': ['koto', 'flute'], 'drums': 'basic', 'piano': 'arp'},
        {'chords': M2_CHORDS, 'melody': M2, 'lead': ['trumpet'], 'bass_pattern': 'sync', 'drums': 'drive', 'pad': True, 'fill': True},
        {'chords': M3_CHORDS, 'melody': M3, 'lead': ['saw', 'flute'], 'transpose': 2, 'drums': 'drive', 'pad': True},
        {'chords': ['F', 'G', 'Am', 'E'], 'piano': 'block', 'drums': 'basic', 'fill': True},
    ]
    return render_song(sections, 150)


def boss_theme():
    sections = [
        {'chords': ['Dm', 'Bb', 'C', 'A'], 'piano': 'arp', 'drums': 'basic', 'pad': True},
        {'chords': M4_CHORDS, 'melody': M4, 'lead': ['square', 'glock'], 'drums': 'drive'},
        {'chords': M5_CHORDS, 'melody': M5, 'lead': ['square', 'glock'], 'drums': 'drive', 'pad': True, 'fill': True},
        {'chords': M4_CHORDS, 'melody': M4, 'lead': ['trumpet', 'glock'], 'piano': 'arp', 'drums': 'basic', 'pad': True},
        {'chords': M5_CHORDS, 'melody': M5, 'lead': ['square', 'trumpet', 'glock'], 'transpose': 2, 'drums': 'drive', 'pad': True},
        {'chords': ['Bb', 'C', 'A', 'A'], 'piano': 'block', 'drums': 'drive', 'fill': True},
    ]
    return render_song(sections, 172)
