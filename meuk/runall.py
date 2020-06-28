# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 17:49:06 2020

@author: super
"""

import cv2
from staffs.seperate_staffs import separate_staffs
from staffs.staff_objects import Staff #, Staff_measure, Bar_line, split_measures
from notes.note_objects import Template, Head#, Stem #, Flag, Rest, Accidental, Dots, Relation
from notes.build_notes_objects import find_stems, build_notes
from template_matching import template_matching

img = cv2.imread('Fmttm.png')

staff_imgs = separate_staffs(img)

staffs = []
for s in staff_imgs:
    staffs.append(Staff(s))
    
threshold = 0.8

temp_staff = staffs[0]
    
template_head = Template('closed head','head-filled.png')
matches_head = template_matching(template_head, temp_staff, threshold)
# template_head.image, template_head.h, template_head.w

head_objects = []
for head in matches_head:
    head_obj = Head(head[0],head[1],template_head)
    head_obj.set_pitch(temp_staff)
    head_objects.append(head_obj)

    
stem_objects = find_stems(temp_staff)

notes = build_notes(head_objects, stem_objects, [], temp_staff)

pitch_list = ['x','G6','F6','E6','D6','C6','B6','A6','G5','F5','E5','D5','C5','B5','A5','G4','F4','E4','D4','C4','B4','A4','G3','F3','E3','D3']
for note in notes:
    print(pitch_list[note.pitch])
    print(note.duration)
    print('\n')
    