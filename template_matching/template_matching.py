from enum import Enum

import cv2
import imutils
import numpy as np

from notes.note_objects import Template


def template_matching(template, staff, threshold):
    img_gray = cv2.cvtColor(staff.image, cv2.COLOR_BGR2GRAY)

    # Resize template to match staff height
    resized_template = imutils.resize(template.value.image, height=int(staff.dist * template.value.height_units))
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


class AvailableTemplates(Enum):
    # Notes
    NoteheadClosed = Template('closed_notehead', 'images/templates/head-filled.png', 1)
    NoteheadOpen = Template('open_notehead', 'images/templates/head-open.jpg', 1)
    FlagUpsideDown = Template('flag_upside_down', 'images/templates/flag.png', 1.5)

    # Rests
    RestFull = Template('full_rest', 'images/templates/rests/full-rest-on-line.jpg', 1)
    # !! Half and full rest are *very* similar templates, maybe these would have to be
    # merged and distinguished in a later step eg. using context
    RestHalf = Template('half_rest', 'images/templates/rests/half-rest-on-line.jpg', 1)
    RestFourth = Template('fourth_rest', 'images/templates/rests/4th-rest-with-lines.jpg', 4)
    RestEighth = Template('eighth_rest', 'images/templates/rests/8th-rest-with-line.jpg', 2)

    # Clefs
    ClefG = Template('g-clef', 'images/templates/g-clef-with-lines.jpg', 7.5)
    ClefF = Template('f-clef', 'images/templates/f-clef-with-lines.jpg', 4)
    ClefC = Template('c-clef', 'images/templates/c-clef-with-lines.jpg', 4)

    # Keys
    Flat = Template('flat', 'images/templates/flat.jpg', 2.4)
    FlatDouble = Template('double_flat', 'images/templates/double-flat.jpg', 2.4)
    Sharp = Template('sharp', 'images/templates/sharp.jpg', 2.8)
    SharpDouble = Template('double_sharp', 'images/templates/double-sharp.jpg', 1)
    Natural = Template('natural', 'images/templates/natural.jpg', 3)

    # Symbols
    Fermate = Template('fermate', 'images/templates/fermate.jpg', 1.5)

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
