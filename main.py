import xml.etree.cElementTree as ET
from typing import List, Dict

import cv2 as cv
import os.path

from denoise.denoise import denoise
from dewarp.dewarp import dewarp
from helpers.measure_helpers import split_measures, find_measure
from helpers.note_helpers import find_pitch
from models.measure import Measure
from models.note_objects import Accidental, Flag, Rest, Head
from models.staff import Staff
from models.staff_objects import Time, Clef, Key
from mxml.xml_from_objects import add_backup, add_note, add_rest, add_measure, create_firstpart, create_xml, add_part
from notes.build_notes_objects import detect_accidentals, group_accidentals, build_notes, find_stems
from notes.find_beams import find_beams
from staffs.connect_staffs import connect_staffs
from staffs.seperate_staffs import separate_staffs
from template_matching.template_matching import AvailableTemplates, template_matching_array
from utils.util import imshow, bgr_imshow
from helpers.staff_fixers import fix_staff_relations


def main():
    INPUT_DIR = 'images/sheets/chorale violin/'
    INPUT_PATH = INPUT_DIR + 'input.png'
    DEWARPED_FILE = 'dewarped.png'
    DEWARPED_PATH = INPUT_DIR + DEWARPED_FILE
    SHOW_STEPS = True
    FORCE_PREPRC = True
    
    # For evaluation
    EVAL = True
    ACTUAL_TIMES = ['4/4 time'] # list of time signatures per instrument (name of template i.e. '2/2 time')
    ACTUAL_CLEFS = ['G'] # list of clef letters per instrument

    # Check if file exists
    if not os.path.isfile(INPUT_PATH):
        raise FileNotFoundError

    # Preprocessing steps
    if os.path.isfile(DEWARPED_PATH) and not FORCE_PREPRC:
        dewarped_img = cv.imread(DEWARPED_PATH, cv.IMREAD_COLOR)
    else:
        original_img = cv.imread(INPUT_PATH, cv.IMREAD_COLOR)
        denoised_img = denoise(original_img, is_rgb=True)
        dewarped_img = dewarp(denoised_img, is_rgb=True)
        imshow(DEWARPED_FILE, dewarped_img)
        cv.imwrite(DEWARPED_PATH, dewarped_img)

    # separate full sheet music into an image for each staff
    staffs = [Staff(s) for s in separate_staffs(dewarped_img)]

    connect_staffs(dewarped_img, staffs)

    # set threshold for template matching
    all_measures: List[Measure] = []
    all_signatures: Dict[int, 'Time'] = {}
    all_clefs: Dict[int, 'Clef'] = {}

    # groepeer maten naar parts
    parts = [s.nr_instrument for s in staffs]
    if None in parts:
        parts = fix_staff_relations(staffs)
    parts = list(set(parts))
    parts.sort()

    for staff_index in range(len(staffs)):
        current_staff: Staff = staffs[staff_index]
        print(f"Staff {staff_index + 1}: {current_staff.nr_timewise}th staff for instrument {current_staff.nr_instrument}")

        if SHOW_STEPS:
            imcopy = current_staff.image.copy()
            for l in current_staff.lines:
                cv.line(imcopy, (l[0], l[1]), (l[2], l[3]), (0,255,255), 1)

        # Generate Time signature objects
        detected_times = template_matching_array(AvailableTemplates.AllTimes.value, current_staff, 0.5)
        time_objects: List['Time'] = []
        for template in detected_times.keys():
            for match in detected_times[template]:
                time_objects.append(Time(match[0], match[1], template))

        if SHOW_STEPS:
            for t in time_objects:
                cv.rectangle(imcopy, (t.x, t.y), (t.x+t.w, t.y+t.h), (255,0,0), 1)

        last_time = None
        if len(detected_times) == 0:
            if current_staff.nr_timewise == 1:
                if EVAL:
                    print(f"no time signature detected for staff {staff_index + 1}")
                    # kan gebruikt worden voor het testen van volgende stappen
                    timedict = {'2/2 time': AvailableTemplates.Time2_2.value, '2/4 time': AvailableTemplates.Time2_4.value, 
                                '3/4 time': AvailableTemplates.Time3_4.value, '3/8 time': AvailableTemplates.Time3_8.value, 
                                '4/4 time': AvailableTemplates.Time4_4.value, '5/4 time': AvailableTemplates.Time5_4.value, 
                                '5/8 time': AvailableTemplates.Time5_8.value, '6/4 time': AvailableTemplates.Time6_4.value, 
                                '6/8 time': AvailableTemplates.Time6_8.value, '7/8 time': AvailableTemplates.Time7_8.value, 
                                '9/8 time': AvailableTemplates.Time9_8.value, '12/8 time': AvailableTemplates.Time12_8.value,
                                '4/4 time C': AvailableTemplates.TimeC.value, 'alla breve': AvailableTemplates.TimeAllaBreve.value}
                    last_time: 'Time' = Time(current_staff.x, current_staff.lines[4][1], timedict[ACTUAL_TIMES[current_staff.nr_instrument-1]])
                else:
                    if SHOW_STEPS:
                        imshow('staff lines and height', imcopy)
                    raise ValueError('OH BOY NO TIME SIGNATURE WAS DETECTED ON THE FIRST LINE SEND HELP')

            else:
                last_time: 'Time' = all_signatures[current_staff.nr_instrument]

            time_objects.append(Time(last_time.x, last_time.y, last_time.template))

        # Store the last used time signature per voice number for potential later use
        all_signatures[current_staff.nr_instrument] = time_objects[-1]

        # find note stems and barlines
        stem_objects, barlines = find_stems(current_staff)

        # now first finding noteheads to weed out some incorrect barline matches
        # do template matching for notes and rests (to do: change to groups)
        matches_noteheads = template_matching_array(AvailableTemplates.AllNoteheads.value, current_staff, 0.7)
        head_objects: List['Head'] = []
        for template in matches_noteheads.keys():
            for match in matches_noteheads[template]:
                head_objects.append(Head(match[0], match[1], template))

        if SHOW_STEPS:
            for h in head_objects:
                cv.rectangle(imcopy, (h.x, h.y), (h.x+h.w, h.y+h.h), (150,255,150), 1)

        delete_barlines = []
        for bar in barlines:
            for h in head_objects:
                if h.x - 2 <= bar.x <= h.x + h.w + 2:
                    delete_barlines.append(bar)
            for t in time_objects:
                if t.x - 2 <= bar.x <= t.x + t.w + 2:
                    delete_barlines.append(bar)
        real_barlines = []
        for bar in barlines:
            if bar not in delete_barlines:
                real_barlines.append(bar)

        if SHOW_STEPS:
            for b in real_barlines:
                cv.line(imcopy, (b.x, b.y1), (b.x, b.y2), (0,0,255), 1)

        measures = split_measures(real_barlines, current_staff)

        current_staff.set_measures(measures)

        # find accidentals
        accidental_objects = detect_accidentals(current_staff, 0.7)

        if SHOW_STEPS:
            for a in accidental_objects:
                cv.rectangle(imcopy, (a.x, a.y), (a.x+a.w, a.y+a.h), (0,255,0), 1)

        # find clef
        clefs = template_matching_array(AvailableTemplates.AllClefs.value, current_staff, 0.5)
        clef_objects: List['Clef'] = []

        if SHOW_STEPS:
            for temp in clefs:
                for loc in clefs[temp]:
                    cv.rectangle(imcopy, (loc[0], loc[1]), (loc[0]+temp.w, loc[1]+temp.h), (255,0,255), 1)

        # because of low threshold: eliminate non-clefs
        for i, template in enumerate(clefs.keys()):
            for match in clefs[template]:
#                overlap = 0
                if find_measure(measures, match[0]) == find_measure(measures, match[0] + template.w):
#                    for h in head_objects:
#                        if match[0] <= h.x <= match[0] + template.w or match[0] <= h.x + h.w <= match[0] + template.w:
#                            overlap += 1
#                            print(h.x, h.y)
#                    if overlap == 0:
                    curr_clef = Clef(match[0], match[1], template)
                    clef_objects.append(curr_clef)



        real_clefs = []
        remove_clefs = []
        for i in range(len(clef_objects)):
            c1 = clef_objects[i]
            c1x1, c1x2 = (c1.x, c1.x + c1.w)

            if i in remove_clefs:
                remove = 1
            else:
                remove = 0

                for j in range(i + 1, len(clef_objects)):
                    c2 = clef_objects[j]
                    c2x1, c2x2 = (c2.x, c2.x + c2.w)
                    if c1x1 <= c2x1 <= c1x2 or c2x1 <= c1x1 <= c2x2:
                        if c1.type != c2.type:
                            if c1.type == 'F_CLEF':
                                if find_pitch(current_staff, c1.x, c1.y) not in range(7, 10):
                                    remove = 1
                                else:
                                    remove_clefs.append(j)
                            elif c2.type == 'F_CLEF':
                                if find_pitch(current_staff, c2.x, c2.y) not in range(7, 10):
                                    remove_clefs.append(j)
                                else:
                                    remove = 1
                        else:
                            remove = 1

            if remove == 0:
                real_clefs.append(c1)

        # Associate accidentals with a certain note
        global_key_per_measure: List[Accidental] = []
        for i, measure in enumerate(measures):
            key_per_measure: List[Accidental] = global_key_per_measure.copy()
            for accidentals in group_accidentals(accidental_objects):
                if len(accidentals) == 0:
                    continue
                if not accidentals[0].is_local:
                    # We encounter a group of key accidentals, update key accordingly
                    global_key_per_measure = accidentals
                for accidental in accidentals:
                    # Update all accidentals that fit in this measure
                    if measure.start < accidental.x < measure.end:
                        accidental.find_note(measure)
                        key_per_measure.append(accidental)

            measure.set_key(Key(key_per_measure))

            prev_clefs = [clef for clef in real_clefs if clef.x < measure.end]

            if len(prev_clefs) == 0:
                if current_staff.nr_timewise == 1 and i==0:
                    if EVAL:
                        print(f"no clef detected for staff {staff_index + 1}")
                        # kan gebruikt worden voor het testen van volgende stappen
                        clefdict = {'G': AvailableTemplates.ClefG.value, 'F': AvailableTemplates.ClefF.value, 'C': AvailableTemplates.ClefC.value}
                        relevant_clef = Clef(measures[0].start, current_staff.lines[4][1], clefdict[ACTUAL_CLEFS[current_staff.nr_instrument-1]])
                    else:
                        if SHOW_STEPS:
                            imshow('detected objects', imcopy)
                        raise ValueError('OH BOY NO CLEF WAS DETECTED AT THE START OF THE FIRST LINE SEND HELP')
                else:
                    last_clef: 'Clef' = all_clefs[current_staff.nr_instrument]
                    relevant_clef = last_clef
            else:
                relevant_clef = max(prev_clefs, key=lambda clef: clef.x)
            all_clefs[current_staff.nr_instrument] = relevant_clef
            measure.set_clef(relevant_clef)
            if relevant_clef.x > measure.start:
                measure.show_clef = True

            prev_times = [time for time in time_objects if time.x < measure.end]
            if len(prev_times) == 0:
#                if current_staff.nr_timewise == 1:
#                    # kan gebruikt worden voor het testen van volgende stappen
##                    relevant_time = Time(measures[0].start, current_staff.lines[4][1], AvailableTemplates.TimeC.value)
#                    if SHOW_STEPS:
#                        imshow('detected objects', imcopy)
#                    raise ValueError('OH BOY NO TIME SIGNATURE WAS DETECTED AT THE START OF THE FIRST LINE SEND HELP')
#                else:
#                    last_time: 'Time' = all_signatures[current_staff.nr_instrument]
                relevant_time = last_time
            else:
                relevant_time = max(prev_times, key=lambda time: time.x)
            all_signatures[current_staff.nr_instrument] = relevant_time
            measure.set_time(relevant_time)

        time_meas = find_measure(measures, time_objects[0].x)
        if time_meas:
            time_meas.show_time = True

        matches_flags = template_matching_array(AvailableTemplates.AllFlags.value, current_staff, 0.5)
        flag_objects: List['Flag'] = []
        for template in matches_flags.keys():
            for match in matches_flags[template]:
                flag_objects.append(Flag(match[0], match[1], template))

        matches_short_rest = template_matching_array(AvailableTemplates.ShortRests.value, current_staff, 0.7)
        matches_long_rest = template_matching_array(AvailableTemplates.LongRests.value, current_staff, 0.9)
        matches_rest = {**matches_short_rest, **matches_long_rest}
        rest_objects: List['Rest'] = []
        for template in matches_rest.keys():
            for match in matches_rest[template]:
                if (match[1] + template.h) < current_staff.lines[0][1] or match[1] > current_staff.lines[-1][1]:
#                    print('rest out of bounds')
                    pass
                else:
                    rest_objects.append(Rest(match[0], match[1], template, current_staff))

        if SHOW_STEPS:
            for r in rest_objects:
                cv.rectangle(imcopy, (r.x, r.y), (r.x+r.w, r.y+r.h), (255,150,0), 1)

        for head_obj in head_objects:
            head_obj.set_pitch(current_staff)  # determine the pitch based on the Staff line locations
            if head_obj.pitch is None:
                continue
            relevant_measure = find_measure(measures, head_obj.x)
            if relevant_measure is not None:
            # also here, first determine its corresponding measure, and use that to set the note
            # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
                head_obj.set_note(relevant_measure)
                head_obj.set_key(find_measure(measures, head_obj.x).key)


        # find note beams
        beam_objects = find_beams(current_staff)

        # for acc in accidental_objects:
        #     print(acc)
        #     print(acc.acc_type)

        # for head in head_objects:
        #     if head.accidental is not None:
        #         print(head.accidental)

        # takes all noteheads, stems and flags, accidentals and the Staff object to determine full notes
        # in future also should take dots, connection ties, etc.
        notes = build_notes(head_objects, stem_objects, flag_objects, beam_objects, accidental_objects,
                            measures, current_staff)

        # sort notes by x, and thus by time (later add rests first)
        notes.sort(key=lambda x: x.x)

        unique_notes = []
        note_coords = []
        for note in notes:
            if (note.x, note.pitch, note.duration) not in note_coords:
                for i in range(-2, 3):
                    note_coords.append((note.x + i, note.pitch, note.duration))
                unique_notes.append(note)

        if SHOW_STEPS:
            for n in unique_notes:
                cv.rectangle(imcopy, (n.x, n.y), (n.x+n.w, n.y+n.h), (150,0,0), 1)
#            imshow('found objects', imcopy)
            cv.imwrite(f"{INPUT_DIR}staff_{staff_index}.png", imcopy)

        # vanaf hier per measure
        for i, meas in enumerate(measures):
            meas.assign_objects(unique_notes, rest_objects)
            meas.find_backups()

        all_measures += measures



    meas_per_part = []
    for i in parts:
        meas_per_part.append([])
    for part in parts:
        last_sign = ''
        for meas in all_measures:
            if meas.staff.nr_instrument == part:
                meas_per_part[part - 1].append(meas)

                if meas.clef.letter == last_sign:
                    meas.show_clef = False
                else:
                    meas.show_clef = True
                    last_sign = meas.clef.letter

    root = create_xml()

    all_parts = []
    for k, part in enumerate(meas_per_part):
        if k == 0:
            all_parts.append(create_firstpart(root, f"Instrument {k + 1}"))
        else:
            all_parts.append(add_part(root, f"Instrument {k + 1}", k + 1))
        for j, meas in enumerate(part):
            voice = 1
            meas1 = add_measure(all_parts[k], meas, j+1)

            for i, obj in enumerate(meas.get_objects()):
                if i in meas.backup_locs:
                    add_backup(meas1, meas.backup_times[i])
                    voice = voice + 1  # hier eigenlijk nog weer op een manier soms terug naar vorige voice
                    if voice == 4: voice = 1
                if obj.type == 'note':
                    if i in meas.chord_locs:
                        add_note(meas1, obj, voice, True)
                    else:
                        add_note(meas1, obj, voice)
                elif obj.type == 'rest':
                    add_rest(meas1, obj, voice)

    tree = ET.ElementTree(root)
    with open(INPUT_DIR+'digitalized.xml', 'wb') as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD '
            'MusicXML 3.1Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">'.encode(
                'utf8'))
        tree.write(f, 'utf-8')

    # TODO: xml voor verschillende parts/instrumenten

    # -------------------------------------


#    voice = 1
#    # write XML file
#    root = create_xml()
#    part1 = create_firstpart(root, "Piano R")
#    for meas in all_measures:
#        meas1 = add_measure(part1, meas)
#
#        for i, obj in enumerate(meas.get_objects()):
#            if i in meas.backup_locs:
#                add_backup(meas1, meas.backup_times[i])
#                voice = voice + 1  # hier eigenlijk nog weer op een manier soms terug naar vorige voice
#            if obj.type == 'note':
#                if i in meas.chord_locs:
#                    add_note(meas1, obj, voice, True)
#                else:
#                    add_note(meas1, obj, voice)
#            elif obj.type == 'rest':
#                add_rest(meas1, obj, voice)
#
#    tree = ET.ElementTree(root)
#
#    with open('mxml/filename.xml', 'wb') as f:
#        f.write(
#            '<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD '
#            'MusicXML 3.1Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">'.encode(
#                'utf8'))
#        tree.write(f, 'utf-8')
    print("Done")

if __name__ == "__main__":
    main()
