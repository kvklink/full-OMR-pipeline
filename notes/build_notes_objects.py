# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 16:52:35 2020

@author: super
"""
import math
from typing import List

import cv2

from notes.note_objects import Stem, Note, Head, Flag, Beam, Accidental
from staffs.staff_objects import Staff


def find_stems(staff: Staff) -> List[Stem]:
    img_bar = staff.image
    img_struct_ver = img_bar.copy()
    ver_size = int(img_bar.shape[0] / 15)
    ver_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_size))
    img_struct_ver2 = cv2.dilate(img_struct_ver, ver_struct, 1)
    img_struct_ver2 = cv2.erode(img_struct_ver2, ver_struct, 1)

    gray_ver = cv2.cvtColor(img_struct_ver2, cv2.COLOR_BGR2GRAY)
    (thresh_ver, im_bw_ver) = cv2.threshold(gray_ver, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    img_canny_ver = im_bw_ver.copy()
    gray2_ver = cv2.cvtColor(img_canny_ver, cv2.COLOR_GRAY2BGR)

    edges2_ver = cv2.Canny(gray2_ver, 100, 200)

    lines2_ver = cv2.HoughLinesP(edges2_ver, 1, math.pi, 1, None, 10,
                                 10)  # edges, rho, theta, threshold, --, minlinelen, maxlinegap

    #    imcopy = img_bar.copy()
    #    for linearr in lines2_ver:
    #        line = linearr[0]
    #        cv2.line(imcopy, (line[0],line[1]),(line[2],line[3]),(0,0,255),2)
    #
    #    cv2.imshow('stems', imcopy)

    stem_list: List[Stem] = []
    for line in lines2_ver:
        l = line[0]
        stem_list.append(Stem(l[0], l[1], l[2], l[3]))

    return stem_list


def find_accidentals(staff: Staff) -> List[Accidental]:
    img_bar = staff.image

    return []  # Stub implementation


def build_notes(heads: List[Head], stems: List[Stem], flags: List[Flag], beams: List[Beam],
                accidentals: List[Accidental], staff: Staff) -> List[Note]:
    dist = staff.dist
    nd = int(dist / 8)

    beam_names = {
        'single_beam': ('eighth', 2),
        'double_beam': ('sixteenth', 4),
        'triple_beam': ('demisemiquaver', 8)
    }

    notes = []

    for head in heads:
        hx1, hy1 = head.x, head.y
        hx2, hy2 = (hx1 + head.w, hy1 + head.h)

        for stem in stems:
            sx1, sy1 = stem.x, stem.y
            sx2, sy2 = (sx1 + stem.w, sy1 + stem.h)

            if sy1 in range(hy1, hy2 + 1) or sy2 in range(hy1, hy2 + 1):
                if sx1 in range(hx1 - nd, hx2 + nd + 1) or sx2 in range(hx1 - nd, hx2 + nd + 1):
                    x_min = min(sx1, sx2, hx1, hx2)
                    x_max = max(sx1, sx2, hx1, hx2)
                    y_min = min(sy1, sy2, hy1, hy2)
                    y_max = max(sy1, sy2, hy1, hy2)

                    head.connect()

                    if head.name == 'closed_notehead':
                        dur = 1
                        durname = 'quarter'
                    elif head.name == 'open_notehead':
                        dur = 2
                        durname = 'half'
                    else:
                        dur = 1
                        durname = 'unknown'
                    notes.append(Note(head, durname, dur * staff.divisions, (x_min, y_min, x_max, y_max)))

        if not head.connected:
            notes.append(Note(head, 'whole', 4 * staff.divisions, (hx1, hy1, hx2, hy2)))

    for note in notes:
        nx1, ny1 = note.x, note.y
        nx2, ny2 = (nx1 + note.w, ny1 + note.h)

        for flag in flags:
            fx1, fy1 = flag.x, flag.y
            fx2, fy2 = (fx1 + flag.w, fy1 + flag.h)

            if fy1 in range(ny1, ny2 + 1) or fy2 in range(ny1, ny2 + 1):
                if fx1 in range(nx1 - nd, nx2 + nd + 1) or fx2 in range(nx1 - nd, nx2 + nd + 1):
                    x_min = min(fx1, fx2, nx1, nx2)
                    x_max = max(fx1, fx2, nx1, nx2)
                    y_min = min(fy1, fy2, ny1, ny2)
                    y_max = max(fy1, fy2, ny1, ny2)

                    new_loc = (x_min, y_min, x_max, y_max)

                    if flag.name in ['flag_upside_down_1', 'flag_1']:
                        div = 2
                        durname = 'eighth'
                    elif flag.name in ['flag_upside_down_2', 'flag_2']:
                        div = 4
                        durname = 'sixteenth'
                    elif flag.name in ['flag_upside_down_3', 'flag_3']:
                        div = 8
                        durname = 'demisemiquaver'
                    else:
                        div = 2
                        durname = 'unknown'

                    note.update_location(new_loc)
                    note.update_duration(durname, int(note.duration / div))

        for beam in beams:
            bx1, by1 = beam.x, beam.y
            bx2, by2 = (bx1 + beam.w, by1 + beam.h)

#            print(by1, by2, ny1, ny2)
#            print(bx1, bx2, nx1, nx2, '\n')

            if by1 in range(ny1 - nd, ny2 + nd) or by2 in range(ny1 - nd, ny2 + nd):
                if bx1 in range(nx1 - nd, nx2 + nd + 1):
                    note.add_beam('begin', beam_names[beam.durname])
                elif bx2 in range(nx1 - nd, nx2 + nd + 1):
                    note.add_beam('end', beam_names[beam.durname])
                elif nx1 > bx1 + nd and nx2 < bx2 - nd:
                    note.add_beam('continue', beam_names[beam.durname])
    # somehow create full notes (check open heads not in note list?)

    return notes
