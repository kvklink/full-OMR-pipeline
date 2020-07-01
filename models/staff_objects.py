# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 15:16:26 2020

@author: super
"""

from enum import Enum, unique

import models.note_objects as note_obj


class Barline:
    def __init__(self, x, y1, y2):
        self.x = x
        self.y1 = y1
        self.y2 = y2


@unique
class ClefTypes(Enum):
    G_CLEF = ('g-clef', 'G')
    F_CLEF = ('f-clef', 'F')
    C_CLEF = ('c-clef', 'C')

    def __init__(self, name: str, letter: str):
        self.name = name
        self.letter = letter

    @staticmethod
    def get_by_name(clef_name: str):
        results = [val.name for val in ClefTypes.__members__.values()]
        if clef_name in results:
            return results[0]
        else:
            raise ValueError(f'{clef_name} is not a valid Clef name!')

    @staticmethod
    def get_by_letter(clef_letter: str):
        results = [val.letter for val in ClefTypes.__members__.values()]
        if clef_letter in results:
            return results[0]
        else:
            raise ValueError(f'{clef_letter} is not a valid Clef letter!')


class Clef:
    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.type = ClefTypes.get_by_name(template.name)
        self.h = template.h
        self.w = template.w


class Key:
    def __init__(self, grouped_accidentals):
        self.x, self.y, self.h, self.w = self.find_rect(grouped_accidentals) if len(grouped_accidentals) > 0 else (
            0, 0, 0, 0)
        self.acc_type = grouped_accidentals[0].acc_type if len(
            grouped_accidentals) > 0 else note_obj.AccidentalTypes.NATURAL
        self.key = self.find_key(grouped_accidentals)
        self.accidentals = grouped_accidentals

    def find_key(self, group):
        amount = len(group)
        if self.acc_type is note_obj.AccidentalTypes.FLAT:
            return -1 * amount
        elif self.acc_type is note_obj.AccidentalTypes.SHARP:
            return amount
        elif amount == 0:
            return 0
        else:
            return float('NaN')


class Time:
    timedict = {'3/4 time': (3, 4), '3/8 time': (3, 8), '4/4 time': (4, 4), '5/4 time': (5, 4), '5/8 time': (5, 8),
                '6/4 time': (6, 4), '6/8 time': (6, 8), '7/8 time': (7, 8), '9/8 time': (9, 8), '12/8 time': (12, 8),
                '4/4 time C': (4, 4)}

    def __init__(self, x, y, template):
        self.beats, self.beat_type = self.timedict[template.name]
        self.x = x
        self.y = y
        self.w = template.w
        self.h = template.h
