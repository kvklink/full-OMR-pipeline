# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 14:16:23 2020

@author: super
"""

import xml.etree.cElementTree as ET

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

def add_measure(part, nr, divs, fifths, beats, beat_type, sign, line):
    measure = ET.SubElement(part, "measure", number=nr)
    # add attributes
    attributes = ET.SubElement(measure, "attributes")
    
    ET.SubElement(attributes, "divisions").text = divs
    
    key = ET.SubElement(attributes, "key")
    ET.SubElement(key, "fifths").text = fifths
    
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = beats
    ET.SubElement(time, "beat-type").text = beat_type
    
    clef = ET.SubElement(attributes, "clef")
    ET.SubElement(clef, "sign").text = sign
    ET.SubElement(clef, "line").text = line
    
    return measure

def add_note(measure, step, octave, dur, ntype):
    # add note
    note1 = ET.SubElement(measure, "note")
    
    pitch1 = ET.SubElement(note1, "pitch")
    ET.SubElement(pitch1, "step").text = step
    ET.SubElement(pitch1, "octave").text = octave
    
    ET.SubElement(note1, "duration").text = dur
    ET.SubElement(note1, "type").text = ntype

def add_rest(measure, dur):
    rest = ET.SubElement(measure, "note")
    ET.SubElement(rest, "rest", measure="yes")
    ET.SubElement(rest, "duration").text = dur
    

root = create_xml()
part1 = create_firstpart(root, "Music")
#part2 = add_part(root, "Piano")
meas1 = add_measure(part1, "1", "1", "0", "4", "4", "G", "2")
add_note(meas1, "C", "4", "2", "half")
add_rest(meas1, "1")
add_note(meas1, "E", "4", "1", "quarter")

# write to file
tree = ET.ElementTree(root)
tree.write("filename.xml")
#
#
#
#
#
#
