# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 17:35:56 2020

@author: super
"""

import xml.etree.cElementTree as ET
import math

def create_xml():
    # create tree
    return ET.Element("score-partwise", version="3.1")

def create_firstpart(root,p1_name):
    # create part-list and add first part
    partlist = ET.SubElement(root,"part-list")
    part_id1 = ET.SubElement(partlist,"score-part", id="P1")
    ET.SubElement(part_id1, "part-name").text = p1_name
    # create part
    part1 = ET.SubElement(root, "part", id="P1")
    
    return part1

def add_part(root, partname):
    # find part-list and add part
    partlist = root.find('part-list')
    part_id = ET.SubElement(partlist,"score-part", id=f"P{len(list(root))}")
    ET.SubElement(part_id, "part-name").text = partname
    # create part
    part = ET.SubElement(root, "part", id=f"P{len(list(root))}")
    
    return part

def add_measure(part, meas):
    measure = ET.SubElement(part, "measure", number=f"{meas.measure}")
    # add attributes
    attributes = ET.SubElement(measure, "attributes")
    
    ET.SubElement(attributes, "divisions").text = f"{meas.divisions}"
    
    key = ET.SubElement(attributes, "key")
    ET.SubElement(key, "fifths").text = f"{meas.key}"
    
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = f"{meas.beats}"
    ET.SubElement(time, "beat-type").text = f"{meas.beat_type}"
    
    clef = ET.SubElement(attributes, "clef")
    ET.SubElement(clef, "sign").text = meas.clef
    ET.SubElement(clef, "line").text = f"{meas.clef_line}"
    
    return measure

def add_note(measure, note):
    # add note
    note1 = ET.SubElement(measure, "note")
    # ET.SubElement(note1, "chord")
    
    pitch1 = ET.SubElement(note1, "pitch")
    ET.SubElement(pitch1, "step").text = note.note
    ET.SubElement(pitch1, "octave").text = f"{note.octave}"
    
    ET.SubElement(note1, "duration").text = f"{note.duration}"
    ET.SubElement(note1, "type").text = note.durname
    
    ET.SubElement(pitch1, "alter").text = "0" if math.isnan(note.accidental) else note.accidental
    # ET.SubElement(note1, "voice").text = ? ("1" oid)
    # ET.SubElement(note1, "staff").text = ? ("1" oid)
    # ET.SubElement(note1, "stem").text = ? ("up" or "down")
    # ET.SubElement(note1, "beam", number=? ("1" oid)).text = ? ("begin" oid)


def add_rest(measure, rest):#dur):
    rest = ET.SubElement(measure, "note")
    ET.SubElement(rest, "rest", measure="yes")
    ET.SubElement(rest, "duration").text = f"{rest.duration}"
    
#
#
#
#
#
#
