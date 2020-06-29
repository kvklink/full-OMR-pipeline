# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 16:08:40 2020

@author: super
"""
from enum import Enum, unique

import cv2

from staffs.staff_objects import Staff_measure


def find_pitch(staff, x, y):
    line_vals = []
    for l in staff.lines:
        line_vals.append(staff.calc_y(l, x))

    if y < min(line_vals):
        print('too high: %d' % y)
        return 'Error'
    elif y > max(line_vals):
        print('too low: %d' % y)
        return 'Error'
    else:
        i = 0
        found = False
        while not found:
            i = i + 1
            found = (y < line_vals[i])

        s = line_vals[i - 1]
        e = line_vals[i]

        if y in range(int(e - staff.dist / 4) + 1, e + 1):
            pitch = line_vals.index(e) * 2
        elif y in range(s, int(s + staff.dist / 4)):
            pitch = line_vals.index(s) * 2
        else:
            pitch = line_vals.index(e) * 2 - 1

    return pitch


class Template:
    def __init__(self, name: str, image, height_units: float = 1):
        self.image = cv2.imread(image, 0) if isinstance(image, str) else image
        self.name = name
        self.height_units = height_units
        self.h = self.image.shape[0]
        self.w = self.image.shape[1]

    def update_size(self, tup):
        self.h, self.w = tup


class Head:
    def __init__(self, x, y, template):
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

    def set_pitch(self, staff):
        mid_x = int(self.x + 0.5 * self.w)
        mid_y = int(self.y + 0.5 * self.h)
        self.pitch = find_pitch(staff, mid_x, mid_y)

    def set_note(self, measure):
        # print(f"pitch: {self.pitch}")
        # print(f"measure notes: {measure.notes}")
        self.note = measure.notes[self.pitch % 7]
        self.octave = measure.octave - int(self.pitch / 7)
        self.measure = measure

    def set_accidental(self, accidental):
        self.accidental = accidental

    def set_key(self, key):
        accidentals = key.accidentals
        for acc in accidentals:
            if acc.note == self.note:
                self.accidental = acc.pitch_change
                break


class Stem:
    def __init__(self, x1, y1, x2, y2):
        self.x = x1
        self.y = y1
        self.w = x2 - x1
        self.h = y2 - y1


class Beam:
    def __init__(self, x1, y1, x2, y2, durname):
        self.x = x1
        self.y = y1
        self.w = x2 - x1
        self.h = y2 - y1
        self.durname = durname


class Flag:
    def __init__(self, x, y, template):
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

    def __init__(self, x, y, template, staff):
        self.type = 'rest'

        self.x = x
        self.y = y
        self.name = template.name
        self.h = template.h
        self.w = template.w

        self.duration = int(self.duration_dict[self.name] * staff.divisions)


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
    def __init__(self, x: int, y: int, template: Template, is_local: bool = True):
        self.x = x
        self.y = y
        self.acc_type = AccidentalTypes.get_by_name(template.name)
        self.h = template.h
        self.w = template.w

        self.note = ''
        self.is_local = is_local

    def find_note(self, measure: Staff_measure):
        pitch = find_pitch(measure.staff, self.x, self.y)
        self.note = measure.notes[pitch % 7]

    def set_is_local(self, is_local: bool):
        self.is_local = is_local


class Dots:
    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.h = template.h
        self.w = template.w


class Relation:
    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.name = template.name
        self.h = template.h
        self.w = template.w


class Note:
    def __init__(self, base, durname, duration, loc):
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

    def update_pitch(self, new_pitch):
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
