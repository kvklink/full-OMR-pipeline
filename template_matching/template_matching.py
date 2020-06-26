from enum import Enum
from typing import Dict, Any, List

import cv2
import imutils
import numpy as np

from notes.note_objects import Template
from staffs.staff_objects import Staff


def template_matching(template: Template, staff: Staff, threshold: float):
    img_gray = cv2.cvtColor(staff.image, cv2.COLOR_BGR2GRAY)

    # Resize template to match staff height
    resized_template = imutils.resize(template.image, height=int(staff.dist * template.height_units))
    template.update_size(resized_template.shape)
#    template.update_size()
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


def template_matching_array(templates: List[Template], staff: Staff, threshold: float) -> Dict[str, List[Any]]:
    result = {}
    for template in templates:
        result[template.name] = template_matching(template, staff, threshold)
    return result


class AvailableTemplates(Enum):
    Barline = Template('barline', 'images/templates/barline.png', 4)

    # Notes
    NoteheadClosed = Template('closed_notehead', 'images/templates/head-filled.png', 1)
    NoteheadOpen = Template('open_notehead', 'images/templates/head-open.png', 1)
    FlagUpsideDown1 = Template('flag_upside_down_1', 'images/templates/flags/down-1.png', 3)
    FlagUpsideDown2 = Template('flag_upside_down_2', 'images/templates/flags/down-2.png', 3)
    FlagUpsideDown3 = Template('flag_upside_down_3', 'images/templates/flags/down-3.png', 4)
    Flag1 = Template('flag_1', 'images/templates/flags/up-1.png', 3)
    Flag2 = Template('flag_2', 'images/templates/flags/up-2.png', 3)
    Flag3 = Template('flag_3', 'images/templates/flags/up-3.png', 4)

    AllNotes = [NoteheadClosed, NoteheadOpen, FlagUpsideDown1]

    # Rests
    RestFull = Template('full_rest', 'images/templates/rests/full-rest-on-line.jpg', 1)
    # !! Half and full rest are *very* similar templates, maybe these would have to be
    # merged and distinguished in a later step eg. using context
    RestHalf = Template('half_rest', 'images/templates/rests/half-rest-on-line.jpg', 1)
    RestFourth = Template('fourth_rest', 'images/templates/rests/4th-rest-with-lines.jpg', 4)
    RestEighth = Template('eighth_rest', 'images/templates/rests/8th-rest-with-line.jpg', 2)

    AllRests = [RestFull, RestHalf, RestFourth, RestEighth]

    # Clefs
#    ClefG = Template('g-clef', 'images/templates/clefs/g-clef-with-lines.jpg', 7.5)
    ClefG = Template('g-clef', 'images/templates/clefs/g-clef-with-lines-2.jpg', 4)
    ClefF = Template('f-clef', 'images/templates/clefs/f-clef-with-lines.jpg', 4)
    ClefC = Template('c-clef', 'images/templates/clefs/c-clef-with-lines.jpg', 4)

    AllClefs = [ClefG, ClefF, ClefC]

    # Keys
    Flat = Template('flat', 'images/templates/accidentals/flat.jpg', 2.4)
    FlatDouble = Template('double_flat', 'images/templates/accidentals/double-flat.jpg', 2.4)
    Sharp = Template('sharp', 'images/templates/accidentals/sharp.jpg', 2.8)
    SharpDouble = Template('double_sharp', 'images/templates/accidentals/double-sharp.jpg', 1)
    Natural = Template('natural', 'images/templates/accidentals/natural.jpg', 3)

    AllKeys = [Flat, FlatDouble, Sharp, SharpDouble, Natural]

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
