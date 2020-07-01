import xml.etree.cElementTree as ET
from typing import List

import cv2 as cv

import models.note_objects as note_obj
import models.staff as s_m
import models.staff_objects as staff_obj
import mxml.xml_from_objects as xml_from_obj
import notes.build_notes_objects as build_objects
import notes.find_beams as beam_find
import staffs.seperate_staffs as staff_separate
import template_matching.template_matching as matching
import helpers.measure_helpers as measure_helpers


def main():
    input_file = 'images/sheets/fmttm/input.png'

    # denoise
    # denoised_image = denoise(cv.imread(input_file))

    # deskew
    # deskewed_image = deskew(denoised_image)
    deskewed_image = cv.imread(input_file)  # temporary

    # separate full sheet music into an image for each staff
    staffs = [s_m.Staff(s) for s in staff_separate.separate_staffs(deskewed_image)]
    temp_staff = staffs[1]  # temporary: do only for first staff while testing

    # set threshold for template matching
    threshold = 0.8

    # time
    times34 = matching.template_matching(matching.AvailableTemplates.Time3_4.value, temp_staff, 0.7)
    time34_objects = []
    for t in times34:
        time34_objects.append(staff_obj.Time(t[0], t[1], matching.AvailableTemplates.Time3_4.value))

    # find measures
    measure_locs = matching.template_matching(matching.AvailableTemplates.Barline.value, temp_staff, 0.8)
    barlines = measure_helpers.select_barlines(measure_locs, temp_staff, matching.AvailableTemplates.Barline.value)
    measures = measure_helpers.split_measures(barlines, temp_staff)

    time_meas = measure_helpers.find_measure(measures, time34_objects[0].x)
    if time_meas is not None:
        time_meas.show_time = True

    # find accidentals
    accidental_objects = build_objects.detect_accidentals(temp_staff, 0.7, time_meas)

    # find clef, key and time
    # clef
    clefs = matching.template_matching(matching.AvailableTemplates.ClefF.value, temp_staff, 0.5)
    clef_objects = []
    for c in clefs:
        clef_objects.append(staff_obj.Clef(c[0], c[1], matching.AvailableTemplates.ClefF.value))

    # temp_acc_group = []
    # if len(temp_acc_group) > 0:
    #     for acc in temp_acc_group:
    #         acc.find_note(measures[0])
    # temp_key = Key(temp_acc_group)

    # Associate accidentals with a certain note
    global_key_per_measure: List[note_obj.Accidental] = []
    # FIXME: iets met global key of ding met maat ofzo zal ik wel missen. help.
    for measure in measures:
        print(measure.key)
        key_per_measure: List[note_obj.Accidental] = global_key_per_measure.copy()
        for accidentals in build_objects.group_accidentals(accidental_objects):
            if not accidentals[0].is_local:
                # We encounter a group of key accidentals, update key accordingly
                global_key_per_measure = accidentals
            for accidental in accidentals:
                # Update all accidentals that fit in this measure
                if measure.start < accidental.x < measure.end:
                    accidental.find_note(measure)
                    key_per_measure.append(accidental)

        measure.set_key(staff_obj.Key(key_per_measure))

        # for now we use first option (temporary) (to do: order clefs/times by x,
        # then add to current measure and following upto next clef/time)
        measure.set_clef(clef_objects[0].type)
        # measure.set_key() # FIXME: wat doet dit? Als in, waar is een Key object voor bedoeld?
        measure.set_time(time34_objects[0])

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
    temp_key = staff_obj.Key(global_key_per_measure)

    # do template matching for notes and rests (to do: change to groups)
    # note heads closed
    matches_head = matching.template_matching(matching.AvailableTemplates.NoteheadClosed.value, temp_staff, threshold)
    matches_head2 = matching.template_matching(matching.AvailableTemplates.NoteheadOpen.value, temp_staff, threshold)

    # single upside down flag
    matches_flag = matching.template_matching(matching.AvailableTemplates.FlagUpsideDown1.value, temp_staff, 0.5)

    matches_rest = matching.template_matching(matching.AvailableTemplates.RestEighth.value, temp_staff, 0.7)

    # turn the found head symbols into objects and add corresponding information
    closed_heads = []
    for head in matches_head:  # for each note head location found with template matching:
        closed_heads.append(
            note_obj.Head(head[0], head[1], matching.AvailableTemplates.NoteheadClosed.value))  # turn into object
    open_heads = []

    for head in matches_head2:
        open_heads.append(note_obj.Head(head[0], head[1], matching.AvailableTemplates.NoteheadOpen.value))

    head_objects = []
    for head_obj in closed_heads:
        head_obj.set_pitch(temp_staff)  # determine the pitch based on the Staff line locations
        if head_obj.pitch == 'Error':
            continue
        temp_measure = measure_helpers.find_measure(measures, head_obj.x)
        # also here, first determine its corresponding measure, and use that to set the note
        # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
        head_obj.set_note(temp_measure)
        head_obj.set_key(temp_key)
        head_objects.append(head_obj)  # show in image
    for head_obj in open_heads:
        head_obj.set_pitch(temp_staff)  # determine the pitch based on the Staff line locations
        if head_obj.pitch == 'Error':
            continue
        temp_measure = measure_helpers.find_measure(measures, head_obj.x)
        # also here, first determine its corresponding measure, and use that to set the note
        # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
        head_obj.set_note(temp_measure)
        head_obj.set_key(temp_key)
        head_objects.append(head_obj)  # show in image

    # turn the found flag symbols into objects
    flag_objects = [note_obj.Flag(flag[0], flag[1], matching.AvailableTemplates.FlagUpsideDown1.value) for flag in
                    matches_flag]

    # turn rest into object
    rest_objects = [note_obj.Rest(rest[0], rest[1], matching.AvailableTemplates.RestEighth.value, temp_staff) for rest
                    in matches_rest]

    # find note stems
    stem_objects = build_objects.find_stems(temp_staff)
    # find note beams
    beam_objects = beam_find.find_beams(temp_staff)

    # takes all noteheads, stems and flags, accidentals and the Staff object to determine full notes
    # in future also should take dots, connection ties, etc.
    notes = build_objects.build_notes(head_objects, stem_objects, flag_objects, beam_objects, accidental_objects,
                                      temp_staff)

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

    voice = 1
    # write XML file
    root = xml_from_obj.create_xml()
    part1 = xml_from_obj.create_firstpart(root, "Piano R")
    for meas in measures:
        meas1 = xml_from_obj.add_measure(part1, meas)

        for i, obj in enumerate(meas.objects):
            if i in meas.backup_locs:
                xml_from_obj.add_backup(meas1, meas.backup_times[i])
                voice = voice + 1  # hier eigenlijk nog weer op een manier soms terug naar vorige voice
            if obj.type == 'note':
                if i in meas.chord_locs:
                    xml_from_obj.add_note(meas1, obj, voice, True)
                else:
                    xml_from_obj.add_note(meas1, obj, voice)
            elif obj.type == 'rest':
                xml_from_obj.add_rest(meas1, obj, voice)
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
