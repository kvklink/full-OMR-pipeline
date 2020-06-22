# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 16:08:40 2020

@author: super
"""

import cv2


def find_pitch(staff, x, y):
    line_vals = []
    for l in staff.lines:
        line_vals.append(staff.calc_y(l, x))

    if y < min(line_vals):
        print('too high: %d' % y)
        return ('Error')
    elif y > max(line_vals):
        print('too low: %d' % y)
        return ('Error')
    else:
        i = 0
        found = False
        while found == False:
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
    def __init__(self, name, image, height_units=1):
        self.image = cv2.imread(image, 0) if isinstance(image, str) else image
        self.name = name
        self.height_units = height_units
        self.h = self.image.shape[0]*height_units
        self.w = self.image.shape[1]*height_units


class Head:
    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.type = template.name
        self.h = template.h
        self.w = template.w

        self.pitch = float('NaN')
        self.note = ''
        self.octave = float('NaN')
        self.accidental = float('NaN')

        self.measure = None

    def set_pitch(self, staff):
        mid_x = int(self.x + 0.5 * self.w)
        mid_y = int(self.y + 0.5 * self.h)
        self.pitch = find_pitch(staff, mid_x, mid_y)

    def set_note(self, measure):
#        print(f"pitch: {self.pitch}")
#        print(f"measure notes: {measure.notes}")
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


class Flag:
    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.type = template.name
        self.h = template.h
        self.w = template.w


class Rest:
    duration_dict = {'full': 1, 'half': 1 / 2, 'quarter': 1 / 4, 'eighth': 1 / 8, 'sixteenth': 1 / 16, 'semidemiquaver': 1 / 32}

    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.type = template.name
        self.h = template.h
        self.w = template.w

        self.duration = self.duration_dict[self.type]


class Accidental:
    pitch_change_dict = {'double_flat': -1, 'flat': -1 / 2, 'natural': 0, 'sharp': 1 / 2, 'double_sharp': 1}

    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.type = template.name
        self.h = template.h
        self.w = template.w

        self.pitch_change = self.pitch_change_dict[self.type]
        self.note = ''

    def find_note(self, measure):
        pitch = find_pitch(measure.staff, self.x, self.y)
        self.note = measure.notes[pitch % 7]


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
        self.type = template.name
        self.h = template.h
        self.w = template.w


class Note:
    def __init__(self, base, durname, duration, loc):
        self.x = loc[0]
        self.y = loc[1]
        self.h = loc[2] - loc[0]
        self.w = loc[3] - loc[1]

        self.pitch = base.pitch
        self.note = base.note
        self.octave = base.octave
        self.durname = durname
        self.duration = duration
        self.accidental = base.accidental

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
        self.h = new_loc[2] - new_loc[0]
        self.w = new_loc[3] - new_loc[1]

    def set_accidental(self, accidental):
        self.accidental = accidental
