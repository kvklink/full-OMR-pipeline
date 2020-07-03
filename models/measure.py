from typing import TYPE_CHECKING, Optional, List, Union

from models.staff_objects import ClefTypes

if TYPE_CHECKING:
    from models.note_objects import Rest, Note
    from models.staff import Staff
    from models.staff_objects import Key, Clef, Time


class Measure:
    note_labels_G = ['G', 'F', 'E', 'D', 'C', 'B', 'A']
    octave_G = 6

    def __init__(self, input_staff: 'Staff', nr: int, start: int, end: int):
        self.lines = input_staff.lines
        self.dist = input_staff.dist

        self.measure = nr
        self.start = start
        self.end = end

        self.show_clef: bool = False
        self.show_key: bool = False
        self.show_time: bool = False

        self.clef: Optional['Clef'] = None
        self.key: Optional['Key'] = None
        self.time: Optional['Time'] = None

        self.clef_line = 2

        self.note_labels = self.note_labels_G
        self.octave = self.octave_G
        self.divisions = input_staff.divisions
        self.staff = input_staff

        self.note_objects: List['Note'] = []
        self.rest_objects: List['Rest'] = []
        self.all_objects: List['Note and Rest'] = []
        self.chord_locs = []
        self.backup_locs = []
        self.backup_times = {}

    def set_clef(self, clef: 'Clef'):
        self.clef = clef
        self.update_clef()

    def set_clef_line(self, clef_line: int):
        self.clef_line = clef_line

    def set_key(self, key: 'Key'):
        self.key = key

    def set_time(self, time: 'Time'):
        self.time = time

    def update_clef(self):
        if self.clef.type == ClefTypes.G_CLEF.name:
            self.clef_line = 2
            self.note_labels = self.note_labels_G
            self.octave = self.octave_G
        elif self.clef.type == ClefTypes.C_CLEF.name:
            self.clef_line = 3
            self.note_labels = self.note_labels_G[6:] + self.note_labels_G[:6]
            self.octave = self.octave_G - 1
        elif self.clef.type == ClefTypes.F_CLEF.name:
            self.clef_line = 4
            self.note_labels = self.note_labels_G[5:] + self.note_labels_G[:5]
            self.octave = self.octave_G - 2
        else:
            raise ValueError(f'{self.clef.type} is an unsupported Clef type')

    def set_divisions(self, div):
        self.divisions = div

    def assign_objects(self, notes: List['Note'], rests: List['Rest']):
        note_objects = [note for note in notes if self.start < note.x < self.end]
        self.note_objects = [obj for obj in note_objects if obj.pitch is not None]
        self.rest_objects = [rest for rest in rests if self.start < rest.x < self.end]
        self.all_objects = sorted(self.note_objects + self.rest_objects, key=lambda x: x.x)
        

    def get_objects(self) -> List[Union['Note', 'Rest']]:
        return self.all_objects

    def find_backups(self):
        objects = self.get_objects()
        for i in range(1, len(objects)):
            obj_1 = objects[i - 1]
            obj_2 = objects[i]
            if obj_1.x + obj_1.w > obj_2.x:
                if obj_1.duration == obj_2.duration:
                    if obj_1.type == obj_2.type == 'note':
                        self.chord_locs.append(i)
                    else:
                        self.backup_locs.append(i)
                        self.backup_times[i] = obj_1.duration
                elif obj_1.duration > obj_2.duration:
                    self.backup_locs.append(i)
                    self.backup_times[i] = obj_1.duration
                else:
                    self.all_objects[i - 1] = obj_2
                    self.all_objects[i] = obj_1
                    # switch objects
                    self.backup_locs.append(i)
                    self.backup_times[i] = obj_2.duration
