import xml.etree.cElementTree as ET
from typing import List

import cv2 as cv

from helpers.measure_helpers import select_barlines, split_measures, find_measure
from models.measure import Measure
from models.note_objects import Accidental, Flag, Rest, Head
from models.staff import Staff
from models.staff_objects import Time, Clef, Key
from mxml.xml_from_objects import add_backup, add_note, add_rest, add_measure, create_firstpart, create_xml
from notes.build_notes_objects import detect_accidentals, group_accidentals, build_notes, find_stems
from notes.find_beams import find_beams
from staffs.seperate_staffs import separate_staffs
from template_matching.template_matching import template_matching, AvailableTemplates, template_matching_array


def main():
    input_file = 'images/sheets/fmttm/input.png'

    # denoise
    # denoised_image = denoise(cv.imread(input_file))

    # deskew
    # deskewed_image = deskew(denoised_image)
    deskewed_image = cv.imread(input_file)  # temporary

    # separate full sheet music into an image for each staff
    # FIXME: 300 iq shit hiero, we pakken nu alleen maar de tweede stem op de eerste regel
    # is met 1 voorteken namelijk interessanter voor mij om te testen dan de eerste stem
    staffs = [[Staff(s) for s in separate_staffs(deskewed_image)][1]]

    # set threshold for template matching
    all_measures: List[Measure] = []

    for current_staff in staffs:
        # Generate Time signature objects
        detected_times = template_matching_array(AvailableTemplates.AllTimes.value, current_staff, 0.7)
        time_objects: List['Time'] = []
        for template in detected_times.keys():
            for match in detected_times[template]:
                time_objects.append(Time(match[0], match[1], template))

        # find measures
        measure_locations = template_matching(AvailableTemplates.Barline.value, current_staff, 0.8)
        barlines = select_barlines(measure_locations, current_staff, AvailableTemplates.Barline.value)
        measures = split_measures(barlines, current_staff)

        time_meas = find_measure(measures, time_objects[0].x)
        time_meas.show_time = True if time_meas else False

        # find accidentals
        accidental_objects = detect_accidentals(current_staff, 0.7)

        # find clef, key and time
        # clef
        clefs = template_matching_array(AvailableTemplates.AllClefs.value, current_staff, 0.5)
        clef_objects: List['Clef'] = []
        for template in clefs.keys():
            for match in clefs[template]:
                clef_objects.append(Clef(match[0], match[1], template))

        # Associate accidentals with a certain note
        global_key_per_measure: List[Accidental] = []
        # FIXME: iets met global key of ding met maat ofzo zal ik wel missen. help.
        for measure in measures:
            key_per_measure: List[Accidental] = global_key_per_measure.copy()
            for accidentals in group_accidentals(accidental_objects):
                if not accidentals[0].is_local:
                    # We encounter a group of key accidentals, update key accordingly
                    global_key_per_measure = accidentals
                for accidental in accidentals:
                    # Update all accidentals that fit in this measure
                    if measure.start < accidental.x < measure.end:
                        accidental.find_note(measure)
                        key_per_measure.append(accidental)

            measure.set_key(Key(key_per_measure))

            # for now we use first option (temporary) (to do: order clefs/times by x,
            # then add to current measure and following upto next clef/time)
            measure.set_clef(clef_objects[0].type)
            # measure.set_key() # FIXME: wat doet dit? Als in, waar is een Key object voor bedoeld?
            measure.set_time(time_objects[0])

        # FIXME: denk ik beter om dit binnen de for loop door alle measures te doen ipv ze per stuk op te zoeken
        # maar ik weet niet zeker of dat wel zomaar kan, vandaar dat ik het zo laat voor nu

        # Sterker nog, clef_meas en key_meas worden nergens anders gebruikt afaik
        # clef_meas = find_measure(measures, clef_objects[0].x)
        # if clef_meas is not None:
        #     clef_meas.show_clef = True
        # key_meas = find_measure(measures, temp_key.x)
        # if key_meas is not None:
        #     key_meas.show_key = True

        # TODO: temp key slaat nergens op. Werkt op dit moment niet met toonsoort-wisselingen of sleutel-wisselingen
        temp_key = Key(global_key_per_measure)

        # do template matching for notes and rests (to do: change to groups)
        # note heads closed
        matches_head = template_matching(AvailableTemplates.NoteheadClosed.value, current_staff, 0.8)
        matches_head2 = template_matching(AvailableTemplates.NoteheadOpen.value, current_staff, 0.8)

        # single upside down flag
        matches_flag = template_matching(AvailableTemplates.FlagUpsideDown1.value, current_staff, 0.5)

        matches_rest = template_matching(AvailableTemplates.RestEighth.value, current_staff, 0.7)

        # turn the found head symbols into objects and add corresponding information
        closed_heads = []
        for head in matches_head:  # for each note head location found with template matching:
            closed_heads.append(Head(head[0], head[1], AvailableTemplates.NoteheadClosed.value))  # turn into object
        open_heads = []

        for head in matches_head2:
            open_heads.append(Head(head[0], head[1], AvailableTemplates.NoteheadOpen.value))

        head_objects = []
        for head_obj in closed_heads:
            head_obj.set_pitch(current_staff)  # determine the pitch based on the Staff line locations
            if head_obj.pitch == 'Error':
                continue
            temp_measure = find_measure(measures, head_obj.x)
            # also here, first determine its corresponding measure, and use that to set the note
            # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
            head_obj.set_note(temp_measure)
            head_obj.set_key(temp_key)
            head_objects.append(head_obj)  # show in image
        for head_obj in open_heads:
            head_obj.set_pitch(current_staff)  # determine the pitch based on the Staff line locations
            if head_obj.pitch == 'Error':
                continue
            temp_measure = find_measure(measures, head_obj.x)
            # also here, first determine its corresponding measure, and use that to set the note
            # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
            head_obj.set_note(temp_measure)
            head_obj.set_key(temp_key)
            head_objects.append(head_obj)  # show in image

        # turn the found flag symbols into objects
        flag_objects = [Flag(flag[0], flag[1], AvailableTemplates.FlagUpsideDown1.value) for flag in
                        matches_flag]

        # turn rest into object
        rest_objects = [Rest(rest[0], rest[1], AvailableTemplates.RestEighth.value, current_staff) for rest
                        in matches_rest]

        # find note stems
        stem_objects = find_stems(current_staff)
        # find note beams
        beam_objects = find_beams(current_staff)

        # takes all noteheads, stems and flags, accidentals and the Staff object to determine full notes
        # in future also should take dots, connection ties, etc.
        notes = build_notes(head_objects, stem_objects, flag_objects, beam_objects, accidental_objects,
                            current_staff)

        # sort notes by x, and thus by time (later add rests first)
        notes.sort(key=lambda x: x.x)

        unique_notes = []
        note_coords = []
        for note in notes:
            if (note.x, note.y) not in note_coords:
                note_coords.append((note.x, note.y))
                unique_notes.append(note)

        # vanaf hier per measure
        for meas in measures:
            meas.assign_objects(unique_notes, rest_objects)
            meas.find_backups()

        all_measures += measures

    voice = 1
    # write XML file
    root = create_xml()
    part1 = create_firstpart(root, "Piano R")
    for meas in all_measures:
        meas1 = add_measure(part1, meas)

        for i, obj in enumerate(meas.objects):
            if i in meas.backup_locs:
                add_backup(meas1, meas.backup_times[i])
                voice = voice + 1  # hier eigenlijk nog weer op een manier soms terug naar vorige voice
            if obj.type == 'note':
                if i in meas.chord_locs:
                    add_note(meas1, obj, voice, True)
                else:
                    add_note(meas1, obj, voice)
            elif obj.type == 'rest':
                add_rest(meas1, obj, voice)
    #
    #    for note in m1_notes:
    #        # bij akkoorden: volgorde maakt niet uit behalve bij verschillende nootlengtes
    #        # in dat geval: sorteren op duur, langste eerst, dan 'backup' (hoe in python?)
    #        add_note(meas1, note)
    #
    # write to file
    tree = ET.ElementTree(root)
    #    tree.write("mxml/filename.xml")

    with open('mxml/filename.xml', 'wb') as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD '
            'MusicXML 3.1Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">'.encode(
                'utf8'))
        tree.write(f, 'utf-8')


if __name__ == "__main__":
    main()
