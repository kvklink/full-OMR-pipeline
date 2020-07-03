from enum import Enum
from typing import Dict, List, TYPE_CHECKING

import cv2
import imutils
import numpy as np

from models.note_objects import AccidentalTypes
from models.staff_objects import ClefTypes
from models.template import Template

if TYPE_CHECKING:
    from models.staff import Staff


def template_matching(template: Template, staff: 'Staff', threshold: float) -> List[List[int]]:
    img_gray = cv2.cvtColor(staff.image, cv2.COLOR_BGR2GRAY)

    # Resize template to match staff height
    resized_template = imutils.resize(template.image, height=int(staff.dist * template.height_units))
    template.update_size(resized_template.shape)
    results = cv2.matchTemplate(img_gray, resized_template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(results >= threshold)

    matches = []
    for pt in zip(*locations[::-1]):
        matches.append([pt[0], pt[1]])

    matches.sort()
    remove_match = []
    for i, pt in enumerate(matches):
        if i in remove_match: continue
        for j in range(i + 1, len(matches)):
            pt2 = matches[j]
            if pt2[0] in range(pt[0] - 4, pt[0] + 4) and pt2[1] in range(pt[1] - 3, pt[1] + 3):
                remove_match.append(pt2)

    unique_matches = [match for match in matches if match not in remove_match]

    return unique_matches


def template_matching_array(templates: List['Template'], staff: 'Staff', threshold: float) -> Dict['Template', List]:
    result = {}
    for template in templates:
        potential_result = template_matching(template, staff, threshold)
        if potential_result:
            result[template] = potential_result

    return result


class AvailableTemplates(Enum):
    # Bar lines
    Barline = Template('barline', 'images/templates/barlines/barline.png', 4)
    BarlineTop = Template('barline', 'images/templates/barlines/barline-top.png', 6)
    BarlineBottom = Template('barline', 'images/templates/barlines/barline-bottom.png', 6)
    BarlineMiddle = Template('barline', 'images/templates/barlines/barline-middle.png', 6)
    BarlineSingle = Template('barline', 'images/templates/barlines/barline-single.png', 6)
    
    AllBarlines = [BarlineTop, BarlineBottom, BarlineMiddle, BarlineSingle]

    # Note heads
    NoteheadClosed = Template('closed_notehead', 'images/templates/noteheads/head-filled.png', 1)
    NoteheadOpen = Template('open_notehead', 'images/templates/noteheads/head-open.png', 1)
    NoteheadOpenWithLine = Template('open_notehead', 'images/templates/noteheads/head-open-line.png', 1)
    NoteWhole = Template('open_notehead', 'images/templates/noteheads/whole-note.png', 1)
    NoteWholeWithLine = Template('open_notehead', 'images/templates/noteheads/whole-note-line.png', 1)

    AllNoteheads = [NoteheadClosed, NoteheadOpen, NoteheadOpenWithLine, NoteWhole, NoteWholeWithLine]

    # Flags
    FlagUpsideDown1 = Template('flag_upside_down_1', 'images/templates/flags/down-1.png', 3)
    FlagUpsideDown1Lines1 = Template('flag_upside_down_1', 'images/templates/flags/down-1-with-lines.png', 3)
    FlagUpsideDown1Lines2 = Template('flag_upside_down_1', 'images/templates/flags/down-1-with-lines2.png', 3)
    FlagUpsideDown2 = Template('flag_upside_down_2', 'images/templates/flags/down-2.png', 3)
    FlagUpsideDown3 = Template('flag_upside_down_3', 'images/templates/flags/down-3.png', 4)
    Flag1 = Template('flag_1', 'images/templates/flags/up-1.png', 3)
    Flag1Lines1 = Template('flag_1', 'images/templates/flags/up-1-with-lines.png', 3)
    Flag1Lines2 = Template('flag_1', 'images/templates/flags/up-1-with-lines2.png', 3)
    Flag2 = Template('flag_2', 'images/templates/flags/up-2.png', 3)
    Flag3 = Template('flag_3', 'images/templates/flags/up-3.png', 4)

    AllFlags = [FlagUpsideDown1, FlagUpsideDown1Lines1, FlagUpsideDown1Lines2, FlagUpsideDown2, FlagUpsideDown3,
                Flag1, Flag1Lines1, Flag1Lines2, Flag2, Flag3]

    AllNotes = AllNoteheads + AllFlags

    # Rests
    RestFull = Template('full_rest', 'images/templates/rests/full-rest-on-line.jpg', 1)
    RestHalf = Template('half_rest', 'images/templates/rests/half-rest-on-line.jpg', 1)
    RestFourth = Template('fourth_rest', 'images/templates/rests/4th-rest-with-lines.jpg', 4)
    RestEighth = Template('eighth_rest', 'images/templates/rests/8th-rest-with-line.jpg', 2)
    RestSixteenth = Template('sixteenth_rest', 'images/templates/rests/16th-rest-with-lines.png', 3)
    RestThirtySecond = Template('thirty_second_rest', 'images/templates/rests/32nd-rest-with-lines.png', 4)

    ShortRests = [RestFourth, RestEighth, RestSixteenth, RestThirtySecond]
    LongRests = [RestFull, RestHalf]
    
    Dot = Template('dot', 'images/templates/punt-halfhoogte.png', 0.5) # nog niet in gebruik

    # Clefs
    #    ClefG = Template('g-clef', 'images/templates/clefs/g-clef-with-lines.jpg', 7.5)
    ClefG = Template(ClefTypes.G_CLEF.name, 'images/templates/clefs/g-clef-with-lines-2.jpg', 4)
    ClefG_full = Template(ClefTypes.G_CLEF.name, 'images/templates/clefs/g-clef-with-lines.jpg', 7.5)
    ClefF = Template(ClefTypes.F_CLEF.name, 'images/templates/clefs/f-clef-with-lines.jpg', 4)
    ClefC = Template(ClefTypes.C_CLEF.name, 'images/templates/clefs/c-clef-with-lines.jpg', 4)

    AllClefs = [ClefG, ClefG_full, ClefF, ClefC]

    # Accidentals
    Flat = Template(AccidentalTypes.FLAT.acc_type, 'images/templates/accidentals/flat.jpg', 2.4)
    FlatDouble = Template(AccidentalTypes.FLAT_DOUBLE.acc_type, 'images/templates/accidentals/double-flat.jpg', 2.4)
    Sharp = Template(AccidentalTypes.SHARP.acc_type, 'images/templates/accidentals/sharp.jpg', 2.8)
    SharpDouble = Template(AccidentalTypes.SHARP_DOUBLE.acc_type, 'images/templates/accidentals/double-sharp.jpg', 1)
    Natural = Template(AccidentalTypes.NATURAL.acc_type, 'images/templates/accidentals/natural.jpg', 3)

    AllAccidentals = [Flat, FlatDouble, Sharp, SharpDouble, Natural]

    # Symbols
    Fermate = Template('fermate', 'images/templates/fermate.jpg', 1.5)

    AllSymbols = [Fermate]

    # Times
    Time3_4 = Template('3/4 time', 'images/templates/times/3_4.jpg', 4)
    Time3_8 = Template('3/8 time', 'images/templates/times/3_8.jpg', 4)
    Time4_4 = Template('4/4 time', 'images/templates/times/4_4.jpg', 4)
    Time5_4 = Template('5/4 time', 'images/templates/times/5_4.jpg', 4)
    Time5_8 = Template('5/8 time', 'images/templates/times/5_8.jpg', 4)
    Time6_4 = Template('6/4 time', 'images/templates/times/6_4.jpg', 4)
    Time6_8 = Template('6/8 time', 'images/templates/times/6_8.jpg', 4)
    Time7_8 = Template('7/8 time', 'images/templates/times/7_8.jpg', 4)
    Time9_8 = Template('9/8 time', 'images/templates/times/9_8.jpg', 4)
    Time12_8 = Template('12/8 time', 'images/templates/times/12_8.jpg', 4)
    TimeAllaBreve = Template('alla breve', 'images/templates/times/alla_breve.jpg', 4)
    TimeC = Template('4/4 time C', 'images/templates/times/c.jpg', 4)

    AllTimes = [Time3_4, Time3_8, Time4_4, Time5_4, Time5_8, Time6_4,
                Time6_8, Time7_8, Time9_8, Time12_8, TimeAllaBreve, TimeC]
