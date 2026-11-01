"""Original acid sequences for Acid MIDI Sequences.

Container lengths, tempos, tonics, and pitch collections are fixed in STUDIES
before any note is written. Seeds identify studies. No stochastic draws.
Offsets are 0. Pitched notes stay in MIDI 36-84. Sequences are monophonic.
Accent is velocity. Glide and filter movement are not encoded.
"""

from __future__ import annotations

from tools.midi_io import BAR_TICKS_4_4, PPQ, bpm_to_us, effective_bpm

GENERATOR_VERSION = "1.0.0"
PACK_ID = "acid-midi-sequences"
PACK_NAME = "Acid MIDI Sequences"
PITCH_LO = 36
PITCH_HI = 84


def _notes(tonic_midi: int, intervals: list[int]) -> list[int]:
    scale = []
    for octave in range(-1, 3):
        for interval in intervals:
            pitch = tonic_midi + octave * 12 + interval
            if PITCH_LO <= pitch <= PITCH_HI:
                scale.append(pitch)
    if len(scale) < 8:
        raise ValueError(f"scale too short from {tonic_midi}")
    return scale


class Part:
    def __init__(self, study, part_id, role, variation, core, channel, file_slug, monophonic, max_poly, collection):
        self.study = study
        self.part_id = part_id
        self.role = role
        self.variation = variation
        self.core = core
        self.channel = channel
        self.file_slug = file_slug
        self.monophonic = monophonic
        self.max_poly = max_poly
        self.collection = collection
        self.container_ticks = study["bars"] * BAR_TICKS_4_4
        self.notes = []

    def add(self, start, duration, pitch, velocity, departure=False):
        end = start + duration
        if start < 0 or duration <= 0 or end > self.container_ticks:
            raise ValueError(f"{self.part_id} boundary {start}+{duration}")
        if not PITCH_LO <= pitch <= PITCH_HI and self.role != "kick-reference":
            raise ValueError(f"{self.part_id} pitch {pitch}")
        if self.role == "kick-reference" and pitch != 36:
            raise ValueError("kick pitch")
        if self.collection is not None and pitch not in self.collection and not departure and self.role != "kick-reference":
            raise ValueError(f"{self.part_id} pitch {pitch} outside collection")
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            overlaps = start < o1 and o0 < end
            if overlaps and (self.monophonic or other["pitch"] == pitch):
                raise ValueError(f"{self.part_id} overlap {pitch}@{start}")
        self.notes.append({
            "nominal_start": start,
            "offset": 0,
            "performed_start": start,
            "duration": duration,
            "pitch": pitch,
            "velocity": velocity,
            "channel": self.channel,
            "departure": departure,
        })

    def finish(self):
        ordered = sorted(self.notes, key=lambda note: (note["performed_start"], note["pitch"]))
        for index, note in enumerate(ordered, start=1):
            note["id"] = f"{self.part_id}.n{index:04d}"
        if self.core and len(ordered) < 8:
            raise ValueError(f"{self.part_id} too short")
        if not ordered:
            raise ValueError(f"{self.part_id} empty")
        return {
            "id": self.part_id,
            "study_id": self.study["id"],
            "slug": self.study["slug"],
            "role": self.role,
            "variation": self.variation,
            "core": self.core,
            "channel": self.channel,
            "file_slug": self.file_slug,
            "path": f"midi/{self.study['slug']}/{self.file_slug}.mid",
            "monophonic": self.monophonic,
            "max_poly": self.max_poly,
            "container_ticks": self.container_ticks,
            "container_bars": self.study["bars"],
            "bpm": self.study["bpm"],
            "tempo_us": self.study["tempo_us"],
            "notes": ordered,
        }


def _step(bar, step):
    return bar * BAR_TICKS_4_4 + step * (PPQ // 4)


def _seq(study, variation):
    return Part(study, f"{study['id']}.seq.{variation}", "acid-sequence", variation, True, 0, f"acid-sequence-{variation}", True, 1, None)


def _harm(study, collection):
    return Part(study, f"{study['id']}.harmonic", "harmonic-reference", None, False, 1, "harmonic-reference", False, 2, collection)


def _kick(study, variation, slug):
    return Part(study, f"{study['id']}.kick.{variation}", "kick-reference", variation, False, 9, slug, True, 1, {36})


def _place(part, hits, gate_for, velocity_for):
    ordered = sorted(hits, key=lambda item: (item[0], item[1]))
    for index, (bar, step, pitch, departure) in enumerate(ordered):
        start = _step(bar, step)
        if index + 1 < len(ordered):
            nxt = ordered[index + 1]
            gap = _step(nxt[0], nxt[1]) - start
        else:
            gap = part.container_ticks - start
        gate = gate_for(bar, step)
        if gate > gap:
            gate = gap
        if gate <= 0:
            raise ValueError(f"{part.part_id} zero gate")
        part.add(start, gate, pitch, velocity_for(bar, step), departure=departure)


def studies():
    rows = [
        {
            "id": "s01", "slug": "s01-offbeat-squelch", "title": "Offbeat Squelch",
            "bpm": 130, "bars": 16, "tonic": "A", "tonal_reference": "A",
            "collection_name": "A natural minor", "pitch_classes": [9, 11, 0, 2, 4, 5, 7],
            "departures": [], "seed": 13001,
            "identity": "Sixteenth-note acid leaves every quarter-note downbeat empty and accents the offbeat. Variation B moves the attacks onto the downbeats and rests the offbeats.",
            "limitations": "Use kick-a with variation A and kick-b with variation B. Glide is not encoded.",
        },
        {
            "id": "s02", "slug": "s02-tresillo-climb", "title": "Tresillo Climb",
            "bpm": 138, "bars": 8, "tonic": "E", "tonal_reference": "E",
            "collection_name": "E Phrygian", "pitch_classes": [4, 5, 7, 9, 11, 0, 2],
            "departures": [], "seed": 13802,
            "identity": "A 3+3+2 sixteenth grid climbs the Phrygian mode. Variation B uses the opposite rest grid and descends.",
            "limitations": "One quarter-note kick is shared. It does not mute the sequence.",
        },
        {
            "id": "s03", "slug": "s03-held-fifth", "title": "Held Fifth",
            "bpm": 125, "bars": 16, "tonic": "D", "tonal_reference": "D",
            "collection_name": "D Dorian", "pitch_classes": [2, 4, 5, 7, 9, 11, 0],
            "departures": [], "seed": 12503,
            "identity": "Variation A holds one note for most of each bar, alternating root and fifth. Variation B breaks those holds into two attacks a fifth apart.",
            "limitations": "The long gates are note durations, not filter movement.",
        },
        {
            "id": "s04", "slug": "s04-short-gate", "title": "Short Gate",
            "bpm": 142, "bars": 8, "tonic": "F#", "tonal_reference": "F#",
            "collection_name": "F# Aeolian", "pitch_classes": [6, 8, 9, 11, 1, 2, 4],
            "departures": [], "seed": 14204,
            "identity": "Variation A is a 90-tick engine that skips the downbeat of even bars. Variation B keeps only the odd sixteenths and a different four-note loop.",
            "limitations": "Kick-a marks the skipped downbeats. Kick-b marks beat 3.",
        },
        {
            "id": "s05", "slug": "s05-question-gap", "title": "Question Gap",
            "bpm": 133, "bars": 16, "tonic": "C", "tonal_reference": "C",
            "collection_name": "C Mixolydian", "pitch_classes": [0, 2, 4, 5, 7, 9, 10],
            "departures": [], "seed": 13305,
            "identity": "Two bars of eighth notes ask a question, then two bars leave a single offbeat answer. Variation B swaps which pair is dense.",
            "limitations": "The kick follows variation A's gaps. Variation B does not keep those gaps.",
        },
        {
            "id": "s06", "slug": "s06-five-cell", "title": "Five Cell",
            "bpm": 145, "bars": 8, "tonic": None, "tonal_reference": "no fixed tonic",
            "collection_name": "pitch-class set {0, 3, 5, 7, 10}", "pitch_classes": [0, 3, 5, 7, 10],
            "departures": ["Variation A bar 7 step 4 substitutes F#3 (54)."],
            "seed": 14506,
            "identity": "A five-pitch cell rotates across a grid that skips two downbeats. Variation B retrogrades the cell on the opposite sixteenths.",
            "limitations": "Kick-a fits variation A. Kick-b fits variation B.",
        },
        {
            "id": "s07", "slug": "s07-raised-seventh", "title": "Raised Seventh",
            "bpm": 128, "bars": 16, "tonic": "Bb", "tonal_reference": "Bb",
            "collection_name": "Bb harmonic minor", "pitch_classes": [10, 0, 1, 3, 5, 6, 9],
            "departures": [], "seed": 12807,
            "identity": "Offbeat sixteenths lean on the raised seventh. Variation B moves those attacks one sixteenth earlier and descends.",
            "limitations": "The raised seventh is a scale tone here, not a departure.",
        },
        {
            "id": "s08", "slug": "s08-dominant-leap", "title": "Dominant Leap",
            "bpm": 136, "bars": 8, "tonic": "G", "tonal_reference": "G",
            "collection_name": "G Phrygian dominant", "pitch_classes": [7, 8, 11, 0, 2, 3, 5],
            "departures": [], "seed": 13608,
            "identity": "The line leaps to the raised third on a syncopated grid. Variation B delays the grid by three sixteenths and answers with a fall.",
            "limitations": "Octave color is written as pitch, not as a synth octave switch.",
        },
    ]
    for row in rows:
        if not 125 <= row["bpm"] <= 145:
            raise ValueError(row["bpm"])
        row["tempo_us"] = bpm_to_us(row["bpm"])
        row["effective_bpm"] = effective_bpm(row["tempo_us"])
        row["meter"] = "4/4"
        row["bar_ticks"] = BAR_TICKS_4_4
        row["ppq"] = PPQ
        row["stochastic_draws"] = 0
    return rows


SCALES = {
    "s01": _notes(45, [0, 2, 3, 5, 7, 8, 10]),
    "s02": _notes(40, [0, 1, 3, 5, 7, 8, 10]),
    "s03": _notes(38, [0, 2, 3, 5, 7, 9, 10]),
    "s04": _notes(42, [0, 2, 3, 5, 7, 8, 10]),
    "s05": _notes(48, [0, 2, 4, 5, 7, 9, 10]),
    "s06": [48, 51, 53, 55, 58, 60, 63, 65, 67, 70, 72],
    "s07": _notes(46, [0, 2, 3, 5, 7, 8, 11]),
    "s08": _notes(43, [0, 1, 4, 5, 7, 8, 10]),
}


def _walk(scale, start, step_index, direction):
    return scale[(start + step_index * direction) % len(scale)]


def _s01(study):
    scale = SCALES["s01"]
    a = _seq(study, "a")
    hits = []
    sounding = 0
    for bar in range(16):
        for step in range(16):
            if step % 4 == 0:
                continue
            if bar >= 12 and step % 2 == 0:
                continue
            degree_cycle = [0, 2, 4, 3, 5, 4, 2, 1]
            hits.append((bar, step, scale[degree_cycle[sounding % 8] + (7 if bar >= 8 else 0)], False))
            sounding += 1
    _place(a, hits, lambda bar, step: 150 if bar < 12 else 200, lambda bar, step: 120 if step % 4 == 2 else 84)

    b = _seq(study, "b")
    hits = []
    sounding = 0
    for bar in range(16):
        for step in (0, 4, 8, 12):
            cycle = [0, 4, 7, 4, 2, 5, 3, 0]
            hits.append((bar, step, scale[cycle[sounding % 8] + (4 if bar >= 8 else 0)], False))
            sounding += 1
    _place(b, hits, lambda bar, step: 220, lambda bar, step: 114 if step == 0 else 78)
    return _with_refs(study, a, b, scale, quarters=True)


def _s02(study):
    scale = SCALES["s02"]
    a = _seq(study, "a")
    hits = []
    sounding = 0
    for bar in range(8):
        for step in (0, 3, 6, 8, 11, 14):
            hits.append((bar, step, scale[(sounding % 7) + (4 if bar % 2 else 0)], False))
            sounding += 1
    _place(a, hits, lambda bar, step: 180, lambda bar, step: 118 if step in (0, 8) else 80)

    b = _seq(study, "b")
    hits = []
    sounding = 0
    for bar in range(8):
        for step in (2, 5, 7, 10, 13, 15):
            hits.append((bar, step, scale[10 - (sounding % 6)], False))
            sounding += 1
    _place(b, hits, lambda bar, step: 140, lambda bar, step: 96)
    return _with_refs(study, a, b, scale, quarters=True, shared_kick=True)


def _s03(study):
    scale = SCALES["s03"]
    a = _seq(study, "a")
    hits = [(bar, 0, scale[0 if bar % 2 == 0 else 4], False) for bar in range(16)]
    _place(a, hits, lambda bar, step: 3000, lambda bar, step: 92 if bar % 2 == 0 else 74)

    b = _seq(study, "b")
    hits = []
    for bar in range(16):
        hits.append((bar, 0, scale[4 if bar % 2 == 0 else 0], False))
        hits.append((bar, 8, scale[7 if bar < 8 else 2], False))
    _place(b, hits, lambda bar, step: 700, lambda bar, step: 110 if step == 0 else 86)
    return _with_refs(study, a, b, scale, quarters=False)


def _s04(study):
    scale = SCALES["s04"]
    a = _seq(study, "a")
    hits = []
    sounding = 0
    cycle = [0, 1, 2, 1, 3, 2, 1, 0]
    for bar in range(8):
        for step in range(16):
            if bar % 2 == 0 and step == 0:
                continue
            hits.append((bar, step, scale[cycle[sounding % 8]], False))
            sounding += 1
    _place(a, hits, lambda bar, step: 90, lambda bar, step: 122 if step % 4 == 2 else 76)

    b = _seq(study, "b")
    hits = []
    sounding = 0
    cycle = [4, 5, 6, 5, 3, 4]
    for bar in range(8):
        for step in range(1, 16, 2):
            hits.append((bar, step, scale[cycle[sounding % 6] + 2], False))
            sounding += 1
    _place(b, hits, lambda bar, step: 160, lambda bar, step: 108)
    return _with_refs(study, a, b, scale, quarters=False, even_downbeats=True)


def _s05(study):
    scale = SCALES["s05"]
    a = _seq(study, "a")
    hits = []
    sounding = 0
    for bar in range(16):
        if bar % 4 < 2:
            steps = (0, 2, 4, 6, 8, 10, 12, 14)
        else:
            steps = (6,)
        for step in steps:
            hits.append((bar, step, scale[(sounding % 6) + (3 if bar >= 8 else 0)], False))
            sounding += 1
    _place(a, hits, lambda bar, step: 200, lambda bar, step: 116 if step == 0 else 82)

    b = _seq(study, "b")
    hits = []
    sounding = 0
    for bar in range(16):
        if bar % 4 >= 2:
            steps = (1, 3, 5, 9, 11, 13)
        else:
            steps = (4, 12)
        for step in steps:
            hits.append((bar, step, scale[8 - (sounding % 5)], False))
            sounding += 1
    _place(b, hits, lambda bar, step: 180, lambda bar, step: 100)
    return _with_refs(study, a, b, scale, quarters=False)


def _s06(study):
    cell = SCALES["s06"][:5]
    collection = set(SCALES["s06"])
    a = _seq(study, "a")
    a.collection = collection
    hits = []
    for bar in range(8):
        seq = cell[bar % 5:] + cell[:bar % 5]
        slots = [step for step in range(16) if step not in (0, 8)]
        for index, step in enumerate(slots):
            pitch = seq[index % 5]
            departure = bar == 6 and step == 4
            if departure:
                pitch = 54
            hits.append((bar, step, pitch, departure))
    _place(a, hits, lambda bar, step: 120, lambda bar, step: 118 if step in (4, 12) else 80)

    b = _seq(study, "b")
    b.collection = collection
    retro = list(reversed(cell))
    hits = []
    for bar in range(8):
        seq = retro[bar % 5:] + retro[:bar % 5]
        for index, step in enumerate((1, 3, 5, 7, 9, 11, 13, 15)):
            hits.append((bar, step, seq[index % 5], False))
    _place(b, hits, lambda bar, step: 100, lambda bar, step: 90)
    harm = _harm(study, collection)
    _add_harm(harm, [cell[0], cell[2], cell[4], cell[1]])
    kick_a = _kick(study, "a", "kick-a")
    kick_b = _kick(study, "b", "kick-b")
    for bar in range(8):
        kick_a.add(_step(bar, 0), 100, 36, 116)
        kick_a.add(_step(bar, 8), 100, 36, 100)
        kick_b.add(_step(bar, 2), 80, 36, 104)
        kick_b.add(_step(bar, 10), 80, 36, 96)
    return [a, b, harm, kick_a, kick_b]


def _s07(study):
    scale = SCALES["s07"]
    a = _seq(study, "a")
    hits = []
    sounding = 0
    cycle = [0, 6, 4, 3, 6, 1, 4, 0]
    for bar in range(16):
        for step in (2, 6, 10, 14):
            hits.append((bar, step, scale[cycle[sounding % 8] + (5 if bar >= 8 else 0)], False))
            sounding += 1
    _place(a, hits, lambda bar, step: 180, lambda bar, step: 124 if step in (2, 10) else 86)

    b = _seq(study, "b")
    hits = []
    sounding = 0
    cycle = [11, 8, 6, 4, 3, 1, 0, 4]
    for bar in range(16):
        for step in (1, 5, 9, 13):
            hits.append((bar, step, scale[cycle[sounding % 8]], False))
            sounding += 1
    _place(b, hits, lambda bar, step: 160, lambda bar, step: 102)
    return _with_refs(study, a, b, scale, quarters=False)


def _s08(study):
    scale = SCALES["s08"]
    a = _seq(study, "a")
    hits = []
    shape = [(0, 0), (1, 1), (3, 4), (4, 0), (6, 7), (8, 4), (11, 1), (14, 0)]
    for bar in range(8):
        lift = 5 if bar in (2, 3, 6, 7) else 0
        for step, degree in shape:
            hits.append((bar, step, scale[degree + lift], False))
    _place(a, hits, lambda bar, step: 160, lambda bar, step: 120 if step in (3, 6) else 84)

    b = _seq(study, "b")
    hits = []
    shape = [(3, 4), (5, 6), (7, 5), (10, 4), (12, 1), (13, 0), (15, 4)]
    for bar in range(8):
        for step, degree in shape:
            hits.append((bar, step, scale[degree + (2 if bar % 2 else 6)], False))
    _place(b, hits, lambda bar, step: 140, lambda bar, step: 110 if step == 3 else 78)
    return _with_refs(study, a, b, scale, quarters=True, shared_kick=True)


def _add_harm(part, pitches):
    spans = [(0, 2), (2, 2), (4, 2), (6, 2)]
    if part.study["bars"] == 16:
        spans = [(0, 4), (4, 4), (8, 4), (12, 4)]
    for index, (bar, length) in enumerate(spans):
        root = pitches[index % len(pitches)]
        fifth = pitches[(index + 1) % len(pitches)]
        if fifth == root:
            fifth = pitches[(index + 2) % len(pitches)]
        part.add(_step(bar, 0), length * BAR_TICKS_4_4, root, 52)
        part.add(_step(bar, 0), length * BAR_TICKS_4_4, fifth, 44)


def _with_refs(study, a, b, scale, quarters, shared_kick=False, even_downbeats=False):
    harm = _harm(study, set(scale))
    _add_harm(harm, [scale[0], scale[4], scale[min(7, len(scale) - 1)], scale[2]])
    if shared_kick:
        kick = _kick(study, "a", "kick-reference")
        for bar in range(study["bars"]):
            for beat in range(4):
                kick.add(_step(bar, beat * 4), 100, 36, 114 if beat == 0 else 96)
        return [a, b, harm, kick]
    kick_a = _kick(study, "a", "kick-a")
    kick_b = _kick(study, "b", "kick-b")
    for bar in range(study["bars"]):
        if even_downbeats:
            if bar % 2 == 0:
                kick_a.add(_step(bar, 0), 160, 36, 116)
            kick_b.add(_step(bar, 8), 140, 36, 108)
        elif quarters:
            for beat in range(4):
                kick_a.add(_step(bar, beat * 4), 100, 36, 116 if beat == 0 else 98)
                kick_b.add(_step(bar, beat * 4 + 2), 80, 36, 104)
        else:
            kick_a.add(_step(bar, 0), 140, 36, 112)
            kick_a.add(_step(bar, 8), 120, 36, 100)
            kick_b.add(_step(bar, 4), 100, 36, 104)
            kick_b.add(_step(bar, 12), 100, 36, 96)
    return [a, b, harm, kick_a, kick_b]


BUILDERS = {
    "s01": _s01, "s02": _s02, "s03": _s03, "s04": _s04,
    "s05": _s05, "s06": _s06, "s07": _s07, "s08": _s08,
}


def _signature(notes):
    return tuple((note["performed_start"], note["pitch"], note["duration"], note["velocity"]) for note in notes)


def _intervals(notes):
    pitches = [note["pitch"] for note in notes]
    return tuple(b - a for a, b in zip(pitches, pitches[1:]))


def _rhythm(notes):
    return tuple(note["performed_start"] for note in notes)


def assert_identities(parts):
    by_study = {}
    for part in parts:
        if part["role"] != "acid-sequence":
            continue
        by_study.setdefault(part["study_id"], {})[part["variation"]] = part
    if len(by_study) != 8:
        raise ValueError("expected 8 studies")
    report = []
    interval_sets = []
    rhythm_sets = []
    for study_id, variations in by_study.items():
        if set(variations) != {"a", "b"}:
            raise ValueError(study_id)
        sig_a = _signature(variations["a"]["notes"])
        sig_b = _signature(variations["b"]["notes"])
        if sig_a == sig_b:
            raise ValueError(f"{study_id} variations match")
        interval_sets.append((study_id, _intervals(variations["a"]["notes"])))
        rhythm_sets.append((study_id, _rhythm(variations["a"]["notes"])))
        report.append({"study_id": study_id, "variation_a_notes": len(sig_a), "variation_b_notes": len(sig_b), "signatures_differ": True})
    rhythms = {}
    for study_id, rhythm in rhythm_sets:
        if rhythm in rhythms:
            raise ValueError(f"{study_id} repeats the rhythm of {rhythms[rhythm]}")
        rhythms[rhythm] = study_id
    return {"studies": report, "method": "variation signatures differ; variation A rhythms are not shared across studies"}


def compose():
    catalog_studies = studies()
    parts = []
    for study in catalog_studies:
        for part in BUILDERS[study["id"]](study):
            parts.append(part.finish())
    identity = assert_identities(parts)
    core = [part for part in parts if part["core"]]
    references = [part for part in parts if not part["core"]]
    if len(core) != 16:
        raise ValueError(f"core count {len(core)}")
    preview_ids = ["s01.seq.a", "s01.harmonic", "s01.kick.a"]
    by_id = {part["id"]: part for part in parts}
    arrangement = {
        "id": "arrangement-preview-s01a",
        "path": "midi/arrangement.mid",
        "format": 1,
        "container_ticks": 16 * BAR_TICKS_4_4,
        "bpm": 130,
        "tempo_us": bpm_to_us(130),
        "meter": "4/4",
        "description": "Study 01 variation A acid sequence with its harmonic reference and kick-a.",
        "tracks": [
            {"name": "Conductor", "source_part": None, "channel": None},
            {"name": "Acid Sequence", "source_part": "s01.seq.a", "channel": 0},
            {"name": "Harmonic Reference", "source_part": "s01.harmonic", "channel": 1},
            {"name": "Kick Reference", "source_part": "s01.kick.a", "channel": 9},
        ],
    }
    catalog = {
        "pack_id": PACK_ID,
        "pack_name": PACK_NAME,
        "catalog_version": GENERATOR_VERSION,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "meter": {"numerator": 4, "denominator": 4, "bar_ticks": BAR_TICKS_4_4},
        "pitched_range": [PITCH_LO, PITCH_HI],
        "c4": 60,
        "note_policy": "note-only MIDI; no program changes, controllers, pitch bend, aftertouch, keyswitches, SysEx, or tuning messages",
        "microtiming": "offset is 0 for every note; performed_start = nominal_start + offset",
        "stochastic_draws": 0,
        "seed_meaning": "Seeds identify studies. The compositions are fully specified and do not draw random values.",
        "glide_note": "Glide and filter motion are not encoded. Accent is velocity. A renderer may map high velocity to a brighter saw, but that mapping is not a MIDI instruction.",
        "core_part_count": len(core),
        "reference_part_count": len(references),
        "studies": [
            {key: study[key] for key in (
                "id", "slug", "title", "bpm", "tempo_us", "effective_bpm", "bars", "meter",
                "bar_ticks", "tonic", "tonal_reference", "collection_name", "pitch_classes",
                "departures", "seed", "identity", "limitations", "stochastic_draws",
            )}
            for study in catalog_studies
        ],
        "parts": [
            {
                "id": part["id"], "study_id": part["study_id"], "role": part["role"],
                "variation": part["variation"], "core": part["core"], "channel": part["channel"],
                "path": part["path"], "notes": len(part["notes"]),
                "container_bars": part["container_bars"], "bpm": part["bpm"],
                "monophonic": part["monophonic"],
            }
            for part in parts
        ],
        "arrangement": arrangement,
        "preview_part_ids": preview_ids,
        "stack_warning": "Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.",
    }
    score = {
        "pack_id": PACK_ID,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "parts": parts,
        "arrangement": arrangement,
        "identity_check": identity,
    }
    # silence unused
    by_id["s01.seq.a"]
    return {"catalog": catalog, "score": score}
