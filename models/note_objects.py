from enum import Enum, unique
from typing import TYPE_CHECKING, Optional

from helpers.note_helpers import find_pitch

if TYPE_CHECKING:
    from models.measure import Measure
    from models.staff import Staff
    from models.staff_objects import Key
    from models.template import Template


@unique
class AccidentalTypes(Enum):
    FLAT = ('flat', -1)
    FLAT_DOUBLE = ('double_flat', -2)
    SHARP = ('sharp', 1)
    SHARP_DOUBLE = ('double_sharp', 2)
    NATURAL = ('natural', 0)

    def __init__(self, acc_type: str, shift: int):
        self.acc_type = acc_type
        self.shift = shift

    @staticmethod
    def get_by_name(acc_type: str) -> 'AccidentalTypes':
        results = [val for val in AccidentalTypes.__members__.values() if acc_type == val.acc_type]
        if len(results) > 0:
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

    def find_note(self, measure: 'Measure'):
        pitch = find_pitch(measure.staff, self.x, self.adjusted_y())
        self.note = measure.note_labels[pitch % 7] if pitch is not None else 'Unknown'

    def set_is_local(self, is_local: bool):
        self.is_local = is_local

    def adjusted_y(self) -> int:
        if self.acc_type in [AccidentalTypes.FLAT, AccidentalTypes.FLAT_DOUBLE]:
            return int(self.y + (self.h * 0.8))
        else:
            return int(self.y + (self.h * 0.5))


class Head:
    def __init__(self, x: int, y: int, template: 'Template'):
        self.x = x
        self.y = y
        self.name = template.name
        self.h = template.h
        self.w = template.w

        self.pitch: Optional[int] = None
        self.note = ''
        self.octave: Optional[int] = None
        self.accidental: Optional['Accidental'] = None

        self.measure = None

        self.connected = False

    def connect(self):
        self.connected = True

    def set_pitch(self, staff: 'Staff'):
        mid_x = int(self.x + 0.5 * self.w)
        mid_y = int(self.y + 0.5 * self.h)
        self.pitch = find_pitch(staff, mid_x, mid_y)

    def set_note(self, measure: 'Measure'):
        self.measure = measure
        self.note = measure.note_labels[self.pitch % 7]
        if measure.clef.letter == 'G':
            self.octave = measure.octave - int((self.pitch+2) / 7)
        elif measure.clef.letter == 'F':
            self.octave = measure.octave - int((self.pitch) / 7)
        elif measure.clef.letter == 'C':
            self.octave = measure.octave - int((self.pitch-1) / 7)

    def set_accidental(self, accidental: Accidental):
        self.accidental = accidental

    def set_key(self, key: 'Key'):
        accidentals = key.accidentals
        for acc in accidentals:
            if acc.note == self.note:
                self.accidental = acc
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


class Rest:
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


class Note:
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
        self.accidental: 'AccidentalTypes' = base.accidental
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

    def set_accidental(self, accidental: 'AccidentalTypes'):
        self.accidental: 'AccidentalTypes' = accidental
