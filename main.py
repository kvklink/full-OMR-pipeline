import xml.etree.cElementTree as ET
from typing import List, Dict

import cv2 as cv
import imutils

from denoise.denoise import denoise
from dewarp.dewarp import dewarp
from helpers.measure_helpers import select_barlines, split_measures, find_measure
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
from template_matching.template_matching import template_matching, AvailableTemplates, template_matching_array
from utils.util import imshow
from helpers.staff_fixers import fix_staff_relations


def main():
    input_folder = 'images/sheets/sonate/'
#    original_img = cv.imread(input_folder+'input.png', cv.IMREAD_COLOR)
#
#    # denoise
#    denoised_image = denoise(original_img, isRgb=True)
#
#    # dewarp
#    dewarped_image = dewarp(denoised_image, isRgb=True)
#    # dewarped_image = cv.imread(input_file, cv.IMREAD_COLOR)  # temporary
##    cv.imwrite(input_folder+'dewarped.png',dewarped_image) 
#    
#    imshow("src", dewarped_image)
    dewarped_image = cv.imread(input_folder+'dewarped.png', cv.IMREAD_COLOR)

    # separate full sheet music into an image for each staff
    staffs = [Staff(s) for s in separate_staffs(dewarped_image)]

    connect_staffs(dewarped_image, staffs)

    # set threshold for template matching
    all_measures: List[Measure] = []
    all_signatures: Dict[int, 'Time'] = {}
    all_clefs: Dict[int, 'Clef'] = {}

    timewises = [s.nr_timewise for s in staffs]
    instruments = [s.nr_instrument for s in staffs]
    print(f"times: {timewises}")
    print(f"instruments: {instruments}")

    # groepeer maten naar parts
    parts = [s.nr_instrument for s in staffs]
    if None in parts:
        parts = fix_staff_relations(staffs)
    parts = list(set(parts))
    parts.sort()

    for staff_index in range(len(staffs)):
        print(staff_index)
        current_staff: Staff = staffs[staff_index]
        
#        #for testing size of template
#        if staff_index == 0:
##            print(current_staff.dist)
#            fclef = cv.imread('images/templates/clefs/hacky-g.png', cv.IMREAD_COLOR)
#            fclef = imutils.resize(fclef, height=int(current_staff.dist * 4))
#            fh, fw = fclef.shape[:2]
#            
#            imf = current_staff.image.copy()
#            ystart = current_staff.lines[4][1]
#            imf[ystart:ystart+fh, 275:275+fw] = fclef
##            imf[ystart:ystart+4*current_staff.dist, 200:300] = (0,0,255)
#            imshow('test', imf)
        
        # Generate Time signature objects
        detected_times = template_matching_array(AvailableTemplates.AllTimes.value, current_staff, 0.5)
        time_objects: List['Time'] = []
        for template in detected_times.keys():
            for match in detected_times[template]:
                time_objects.append(Time(match[0], match[1], template))

        if len(detected_times) == 0:
            if current_staff.nr_timewise == 1:
                raise ValueError('OH BOY NO TIME SIGNATURE WAS DETECTED ON THE FIRST LINE SEND HELP')

            last_time: 'Time' = all_signatures[current_staff.nr_instrument]

            # I really hope y isn't really used, and having x == 0 is okay
            time_objects.append(Time(0, last_time.y, last_time.template))

        # Store the last used time signature per voice number for potential later use
        all_signatures[current_staff.nr_instrument] = time_objects[-1]

#        measure_locations = template_matching(AvailableTemplates.Barline.value, current_staff, 0.8)
#        barlines = select_barlines(measure_locations, current_staff, AvailableTemplates.Barline.value)

        # find note stems and barlines
        stem_objects, barlines = find_stems(current_staff)
        

        # now first finding noteheads to weed out some incorrect barline matches
        # do template matching for notes and rests (to do: change to groups)
        matches_noteheads = template_matching_array(AvailableTemplates.AllNoteheads.value, current_staff, 0.7)
        head_objects: List['Head'] = []
        for template in matches_noteheads.keys():
            for match in matches_noteheads[template]:
                head_objects.append(Head(match[0], match[1], template))

        delete_barlines = []
        for bar in barlines:
            for h in head_objects:
                if h.x - 2 <= bar.x <= h.x + h.w + 2:
                    delete_barlines.append(bar)
        real_barlines = []
        for bar in barlines:
            if bar not in delete_barlines:
                real_barlines.append(bar)

        measures = split_measures(real_barlines, current_staff)

        current_staff.set_measures(measures)

        # find accidentals
        accidental_objects = detect_accidentals(current_staff, 0.7)

        # find clef
        clefs = template_matching_array(AvailableTemplates.AllClefs.value, current_staff, 0.5)
        clef_objects: List['Clef'] = []

        # because of low threshold: eliminate non-clefs
        for i, template in enumerate(clefs.keys()):
            for match in clefs[template]:
                overlap = 0
                if find_measure(measures, match[0]) == find_measure(measures, match[0] + template.w):
                    for h in head_objects:
                        if match[0] <= h.x <= match[0] + template.w or match[0] <= h.x + h.w <= match[0] + template.w:
                            overlap += 1
                    if overlap == 0:
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
        for measure in measures:
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
                if current_staff.nr_timewise == 1:
                    relevant_clef = Clef(measures[0].start, current_staff.lines[4][1], AvailableTemplates.ClefG.value)
#                    raise ValueError('OH BOY NO CLEF WAS DETECTED AT THE START OF THE FIRST LINE SEND HELP')
                    # even uitgezet voor het testen van volgende stappen
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
                if current_staff.nr_timewise == 1:
                    relevant_time = Time(measures[0].start, current_staff.lines[4][1], AvailableTemplates.TimeC.value)
                    # hacky oplossing voor nu
                else:
                    last_time: 'Time' = all_signatures[current_staff.nr_instrument]
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
                    print('rest out of bounds')
                else:
                    rest_objects.append(Rest(match[0], match[1], template, current_staff))

        for head_obj in head_objects:
            head_obj.set_pitch(current_staff)  # determine the pitch based on the Staff line locations
            if head_obj.pitch is None:
                continue
            relevant_measure = find_measure(measures, head_obj.x)
            # also here, first determine its corresponding measure, and use that to set the note
            # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
            head_obj.set_note(relevant_measure)
            head_obj.set_key(find_measure(measures, head_obj.x).key)

        
        # find note beams
        beam_objects = find_beams(current_staff)

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

        # vanaf hier per measure
        for i, meas in enumerate(measures):
            meas.assign_objects(unique_notes, rest_objects)
            meas.find_backups()

        # imcopy = current_staff.image.copy()
        # for n in accidentals:
        #     cv.rectangle(imcopy, (n.x, n.y), (n.x + n.w, n.y + n.h), (255, 0, 0), 2)
        #     cv.line(imcopy, (n.x, int(n.adjusted_y())), (n.x + n.w, int(n.adjusted_y())), (0, 255, 0), 2)
        # imshow(f'{n.note}    {n.x}', imcopy)

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
            meas1 = add_measure(all_parts[k], meas, j + 1)

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
    with open(input_folder+'digitalized.xml', 'wb') as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD '
            'MusicXML 3.1Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">'.encode(
                'utf8'))
        tree.write(f, 'utf-8')

    print("Done")


if __name__ == "__main__":
    main()
