from enum import Enum, unique
from typing import TYPE_CHECKING

from helpers.note_helpers import find_pitch

if TYPE_CHECKING:
    from models.measure import Measure
    from models.staff import Staff
    from models.template import Template


@unique
class AccidentalTypes(Enum):
    FLAT = ('flat', -0.5)
    FLAT_DOUBLE = ('double_flat', -1)
    SHARP = ('sharp', 0.5)
    SHARP_DOUBLE = ('double_sharp', 1)
    NATURAL = ('natural', 0)

    def __init__(self, acc_type: str, shift: float):
        self.acc_type = acc_type
        self.shift = shift

    @staticmethod
    def get_by_name(acc_type: str):
        results = [val.acc_type for val in AccidentalTypes.__members__.values()]
        if acc_type in results:
            return results[0]
        else:
            raise ValueError(f'{acc_type} is not a valid Accidental type!')


class Accidental:
    def __init__(self, x: int, y: int, template: 'Template', is_local: bool = True):
        self.x = x
        self.y = y
        self.acc_type = AccidentalTypes.get_by_name(template.name)
        self.h = template.h
        self.w = template.w

        self.note = ''
        self.is_local = is_local

    def find_note(self, measure):
        pitch = find_pitch(measure.staff, self.x, self.y)
        self.note = measure.notes[pitch % 7]

    def set_is_local(self, is_local: bool):
        self.is_local = is_local


class Spacial:
    # Class that doesn't do anything except for allow to type hint more generally
    # Pretty much anything that takes up beats in a measure goes here
    pass


class Head:
    def __init__(self, x: int, y: int, template: 'Template'):
        self.x = x
        self.y = y
        self.name = template.name
        self.h = template.h
        self.w = template.w

        self.pitch = float('NaN')
        self.note = ''
        self.octave = float('NaN')
        self.accidental = float('NaN')

        self.measure = None

        self.connected = False

    def connect(self):
        self.connected = True

    def set_pitch(self, staff: 'Staff'):
        mid_x = int(self.x + 0.5 * self.w)
        mid_y = int(self.y + 0.5 * self.h)
        self.pitch = find_pitch(staff, mid_x, mid_y)

    def set_note(self, measure: 'Measure'):
        # print(f"pitch: {self.pitch}")
        # print(f"measure notes: {measure.notes}")
        self.note = measure.notes[self.pitch % 7]
        self.octave = measure.octave - int(self.pitch / 7)
        self.measure = measure

    def set_accidental(self, accidental: Accidental):
        self.accidental = accidental

    def set_key(self, key):
        accidentals = key.accidentals
        for acc in accidentals:
            if acc.note == self.note:
                self.accidental = acc.pitch_change
                break


class Stem:
    def __init__(self, x1: int, y1: int, x2: int, y2: int):
        self.x = x1
        self.y = y1
        self.w = x2 - x1
        self.h = y2 - y1


class Beam:
    def __init__(self, x1: int, y1: int, x2: int, y2: int, durname: str):
        self.x = x1
        self.y = y1
        self.w = x2 - x1
        self.h = y2 - y1
        self.durname = durname


class Flag:
    def __init__(self, x: int, y: int, template: 'Template'):
        self.x = x
        self.y = y
        self.name = template.name
        self.h = template.h
        self.w = template.w


class Rest(Spacial):
    duration_dict = {
        'full_rest': 4,
        'half_rest': 2,
        'fourth_rest': 1,
        'eighth_rest': 1 / 2,
        'sixteenth_rest': 1 / 4,
        'semidemiquaver_rest': 1 / 8
    }

    def __init__(self, x: int, y: int, template: 'Template', staff: 'Staff'):
        self.type = 'rest'

        self.x = x
        self.y = y
        self.name = template.name
        self.h = template.h
        self.w = template.w

        self.duration = int(self.duration_dict[self.name] * staff.divisions)


class Dots:
    def __init__(self, x: int, y: int, template: 'Template'):
        self.x = x
        self.y = y
        self.h = template.h
        self.w = template.w


class Relation:
    def __init__(self, x: int, y: int, template: 'Template'):
        self.x = x
        self.y = y
        self.name = template.name
        self.h = template.h
        self.w = template.w


class Note(Spacial):
    def __init__(self, base, durname: str, duration: int, loc: (int, int, int, int)):
        self.type = 'note'

        self.x = loc[0]
        self.y = loc[1]
        self.w = loc[2] - loc[0]
        self.h = loc[3] - loc[1]

        self.pitch = base.pitch
        self.note = base.note
        self.octave = base.octave
        self.durname = durname
        self.duration = int(duration)
        self.accidental = base.accidental
        self.beam = False

    def add_beam(self, relation, dur_info):
        self.beam = relation
        self.durname = dur_info[0]
        self.duration = int(self.duration / dur_info[1])

    def update_pitch(self, new_pitch: float):
        self.pitch = new_pitch
        # +/- 0.5 in de class of aparte functie?

    def update_note(self, new_note):
        self.note = new_note
        # vinden ahv pitch in de class of aparte functie?

    def update_octave(self, new_octave):
        self.octave = new_octave
        # vinden ahv pitch in de class of aparte functie?

    def update_duration(self, durname, new_dur):
        self.durname = durname
        self.duration = new_dur
        # *0.5 in de class of aparte functie?

    def update_location(self, new_loc):
        self.x = new_loc[0]
        self.y = new_loc[1]
        self.w = new_loc[2] - new_loc[0]
        self.h = new_loc[3] - new_loc[1]

    def set_accidental(self, accidental):
        self.accidental = accidental
