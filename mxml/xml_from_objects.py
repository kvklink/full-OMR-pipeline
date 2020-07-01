# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 17:35:56 2020

@author: super
"""

import math
import xml.etree.cElementTree as ET


def create_xml():
    # create tree
    return ET.Element("score-partwise", version="3.1")


def create_firstpart(root, p1_name):
    # create part-list and add first part
    part_list = ET.SubElement(root, "part-list")
    part_id1 = ET.SubElement(part_list, "score-part", id="P1")
    ET.SubElement(part_id1, "part-name").text = p1_name
    # create part
    part1 = ET.SubElement(root, "part", id="P1")

    return part1


def add_part(root, partname):
    # find part-list and add part
    part_list = root.find('part-list')
    part_id = ET.SubElement(part_list, "score-part", id=f"P{len(list(root))}")
    ET.SubElement(part_id, "part-name").text = partname
    # create part
    part = ET.SubElement(root, "part", id=f"P{len(list(root))}")

    return part


def add_measure(part, meas):
    measure = ET.SubElement(part, "measure", number=f"{meas.measure}")
    # add attributes
    attributes = ET.SubElement(measure, "attributes")

    ET.SubElement(attributes, "divisions").text = f"{meas.divisions}"

    if meas.show_key:
        key = ET.SubElement(attributes, "key")
        ET.SubElement(key, "fifths").text = f"{meas.key}"

    if meas.show_time:
        time = ET.SubElement(attributes, "time")
        ET.SubElement(time, "beats").text = f"{meas.time.beats}"
        ET.SubElement(time, "beat-type").text = f"{meas.time.beat_type}"

    if meas.show_clef:
        clef = ET.SubElement(attributes, "clef")
        ET.SubElement(clef, "sign").text = meas.clef
        ET.SubElement(clef, "line").text = f"{meas.clef_line}"

    return measure


def add_note(measure, note, voice, addchord=False):
    # add note
    note1 = ET.SubElement(measure, "note")

    if addchord:
        ET.SubElement(note1, "chord")

    pitch1 = ET.SubElement(note1, "pitch")
    ET.SubElement(pitch1, "step").text = note.note
    ET.SubElement(pitch1, "octave").text = f"{note.octave}"

    ET.SubElement(note1, "duration").text = f"{note.duration}"
    ET.SubElement(note1, "type").text = note.durname
    ET.SubElement(note1, "voice").text = f"{voice}"

    ET.SubElement(pitch1, "alter").text = "0" if math.isnan(note.accidental) else note.accidental
    # ET.SubElement(note1, "voice").text = ? ("1" oid)
    # ET.SubElement(note1, "staff").text = ? ("1" oid)
    # ET.SubElement(note1, "stem").text = ? ("up" or "down")
    if note.beam:
        ET.SubElement(note1, "beam", number="1").text = note.beam


def add_rest(measure, rest, voice):  # dur):
    rest1 = ET.SubElement(measure, "note")
    ET.SubElement(rest1, "rest", measure="yes")
    ET.SubElement(rest1, "duration").text = f"{int(rest.duration)}"
    ET.SubElement(rest1, "voice").text = f"{voice}"


def add_backup(measure, length):
    backup = ET.SubElement(measure, "backup")
    ET.SubElement(backup, "duration").text = f"{int(length)}"
