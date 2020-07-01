import models.staff as staff_model


class Measure:
    Gnotes = ['G', 'F', 'E', 'D', 'C', 'B', 'A']
    Goctave = 6

    def __init__(self, input_staff: staff_model.Staff, nr: int, start: int, end: int):
        self.lines = input_staff.lines
        self.dist = input_staff.dist

        self.measure = nr
        self.start = start
        self.end = end

        self.show_clef = False
        self.show_key = False
        self.show_time = False

        self.clef = 'G'
        self.clef_line = 2

        self.key = 0

        self.beats = 4
        self.beat_type = 4

        self.notes = self.Gnotes
        self.octave = self.Goctave
        self.divisions = input_staff.divisions
        self.staff = input_staff

        self.objects = []
        self.chord_locs = []
        self.backup_locs = []
        self.backup_times = {}

    def set_clef(self, clef):
        self.clef = clef

    def set_clef_line(self, clef_line):
        self.clef_line = clef_line

    def set_key(self, key):
        self.key = key

    def set_beats(self, beats):
        self.beats = beats

    def set_beat_type(self, beat_type):
        self.beat_type = beat_type

    def set_time(self, time):
        self.beats = time.beats
        self.beat_type = time.beat_type

    def update_clef(self):
        if self.clef == 'G':
            self.clef_line = 2
            self.notes = self.Gnotes
            self.octave = self.Goctave
        elif self.clef == 'C':
            self.clef_line = 3
            self.notes = self.Gnotes[6:] + self.Gnotes[:6]
            self.octave = self.Goctave - 1
        elif self.clef == 'F':
            self.clef_line = 4
            self.notes = self.Gnotes[5:] + self.Gnotes[:5]
            self.octave = self.Goctave - 2

    def set_divisions(self, div):
        self.divisions = div

    def assign_objects(self, notes, rests):
        m1_notes = [note for note in notes if self.start < note.x < self.end]
        m1_rests = [rest for rest in rests if self.start < rest.x < self.end]
        m1_objects = m1_notes + m1_rests
        self.objects = sorted(m1_objects, key=lambda x: x.x)

    def find_backups(self):
        for i in range(1, len(self.objects)):
            obj_1 = self.objects[i - 1]
            obj_2 = self.objects[i]
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
                    self.objects[i - 1] = obj_2
                    self.objects[i] = obj_1
                    # switch objects
                    self.backup_locs.append(i)
                    self.backup_times[i] = obj_2.duration
