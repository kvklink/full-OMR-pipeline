import xml.etree.cElementTree as ET

import cv2 as cv

from mxml.xml_from_objects import create_xml, create_firstpart, add_measure, add_note  # , add_part, add_rest
from notes.build_notes_objects import find_stems, build_notes, detect_accidentals
from notes.find_beams import find_beams
from notes.note_objects import Head, Flag
from staffs.seperate_staffs import separate_staffs
from staffs.staff_objects import Staff, find_measure, Clef, Key, Time, split_measures, select_barlines
from template_matching.template_matching import template_matching, AvailableTemplates


def main():
    input_file = 'images/sheets/fmttm/input.png'

    # denoise
    # denoised_image = denoise(cv.imread(input_file))

    # deskew
    # deskewed_image = deskew(denoised_image)
    deskewed_image = cv.imread(input_file)  # temporary

    # separate full sheet music into an image for each staff
    staffs = [Staff(s) for s in separate_staffs(deskewed_image)]
    temp_staff = staffs[0]  # temporary: do only for first staff while testing

    # set threshold for template matching
    threshold = 0.8

    # find measures
    measure_locs = template_matching(AvailableTemplates.Barline.value, temp_staff, 0.8)
    barlines = select_barlines(measure_locs, temp_staff, AvailableTemplates.Barline.value)
    measures = split_measures(barlines, temp_staff)

    # find clef, key and time
    # clef
    clefs = template_matching(AvailableTemplates.ClefG.value, temp_staff, 0.5)
    clef_objects = []
    for c in clefs:
        clef_objects.append(Clef(c[0], c[1], AvailableTemplates.ClefG.value))
    # key, TODO: by template matching (find groups)
    temp_acc_group = []
    if len(temp_acc_group) > 0:
        for acc in temp_acc_group:
            acc.find_note(measures[0])
    temp_key = Key(temp_acc_group)
    # time
    times34 = template_matching(AvailableTemplates.Time3_4.value, temp_staff, 0.7)
    time34_objects = []
    for t in times34:
        time34_objects.append(Time(t[0], t[1], AvailableTemplates.Time3_4.value))

    # for now we use first option (temporary) (to do: order clefs/times by x,
    # then add to current measure and following upto next clef/time)
    for meas in measures:
        meas.set_clef(clef_objects[0].type)
        meas.set_key(temp_key.key)
        meas.set_time(time34_objects[0])

    # do template matching for notes and rests (to do: change to groups)
    # note heads closed
    matches_head = template_matching(AvailableTemplates.NoteheadClosed.value, temp_staff, threshold)
    matches_head2 = template_matching(AvailableTemplates.NoteheadOpen.value, temp_staff, threshold)

    # single upside down flag
    matches_flag = template_matching(AvailableTemplates.FlagUpsideDown1.value, temp_staff, 0.5)

    # turn the found head symbols into objects and add corresponding information
    closed_heads = []
    for head in matches_head:  # for each note head location found with template matching:
        closed_heads.append(Head(head[0], head[1], AvailableTemplates.NoteheadClosed.value))  # turn into object
    open_heads = []

    for head in matches_head2:
        open_heads.append(Head(head[0], head[1], AvailableTemplates.NoteheadOpen.value))

    head_objects = []
    for head_obj in closed_heads:
        head_obj.set_pitch(temp_staff)  # determine the pitch based on the Staff line locations
        if head_obj.pitch == 'Error': continue
        temp_measure = find_measure(measures, head_obj.x)
        # also here, first determine its corresponding measure, and use that to set the note
        # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
        head_obj.set_note(temp_measure)
        head_obj.set_key(temp_key)
        head_objects.append(head_obj)  # show in image
    for head_obj in open_heads:
        head_obj.set_pitch(temp_staff)  # determine the pitch based on the Staff line locations
        if head_obj.pitch == 'Error': continue
        temp_measure = find_measure(measures, head_obj.x)
        # also here, first determine its corresponding measure, and use that to set the note
        # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
        head_obj.set_note(temp_measure)
        head_obj.set_key(temp_key)
        head_objects.append(head_obj)  # show in image

    # turn the found flag symbols into objects
    flag_objects = [Flag(flag[0], flag[1], AvailableTemplates.FlagUpsideDown1.value) for flag in matches_flag]

    # find note stems
    stem_objects = find_stems(temp_staff)
    # find note beams
    beam_objects = find_beams(temp_staff)

    # find accidentals
    accidental_objects = detect_accidentals(temp_staff, threshold)

    # takes all noteheads, stems and flags, accidentals and the Staff object to determine full notes
    # in future also should take dots, connection ties, etc.
    notes = build_notes(head_objects, stem_objects, flag_objects, beam_objects, accidental_objects, temp_staff)

    # sort notes by x, and thus by time (later add rests first)
    notes.sort(key=lambda x: x.x)

    unique_notes = []
    note_coords = []
    for note in notes:
        if (note.x, note.y) not in note_coords:
            note_coords.append((note.x, note.y))
            unique_notes.append(note)

    # select only notes for first measure (should later be done for each measure and maybe add list to the measure)
    m1_notes = [note for note in unique_notes if note.x < measures[0].end]

    # write XML file
    root = create_xml()
    part1 = create_firstpart(root, "Piano R")
    meas1 = add_measure(part1, measures[0])
    # even voor het opvangen van niet zoeken naar rests:
    rest = ET.SubElement(meas1, "note")
    ET.SubElement(rest, "rest", measure="yes")
    ET.SubElement(rest, "duration").text = "6"

    for note in m1_notes:
        # bij akkoorden: volgorde maakt niet uit behalve bij verschillende nootlengtes
        # in dat geval: sorteren op duur, langste eerst, dan 'backup' (hoe in python?)
        add_note(meas1, note)

    # write to file
    tree = ET.ElementTree(root)
    #    tree.write("mxml/filename.xml")

    with open('mxml/filename2.xml', 'wb') as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD '
            'MusicXML 3.1Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">'.encode(
                'utf8'))
        tree.write(f, 'utf-8')


if __name__ == "__main__":
    main()
