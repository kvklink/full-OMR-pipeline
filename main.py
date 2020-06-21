import cv2 as cv
import numpy as np

from notes.build_notes_objects import find_stems, build_notes
from notes.note_objects import Template, Head, Stem, Flag, Rest, Accidental, Dots, Relation
from staffs.seperate_staffs import seperate_staffs
from staffs.staff_objects import Staff, Staff_measure, find_measure, Clef, Key, Time, Bar_line, split_measures
from template_matching.template_matching import template_matching, AvailableTemplates

from mxml.xml_from_objects import *

# from denoise.denoise import denoise
# from template_matching.template_matching import template_matching

def main():
    input = 'images/sheets/Fmttm.png'

    # returnt een binary image, maar de volgende functies hebben een rgb of grayscale image nodig om goed te werken
    #    denoised_image = denoise(input)

    # seperate full sheet music into an image for each staff
    # (input=rgb (grayscale also possible with slight adjustment in function))
    staff_imgs = seperate_staffs(cv.imread(input))

    # create list of Staff objects, by creating Staff objects of the staff images
    staffs = []
    for s in staff_imgs:
        staffs.append(Staff(s))

    temp_staff = staffs[0]  # do only for first staff while testing
    
    # set threshold for template matching
    threshold = 0.8 

    # create a Template object with object name and image filename
    template_head = Template('closed head', 'images/templates/head-filled.png')
    # resize template with respect to temp_staff.dist (i.e. head has height of dist)
    # do template matching with the Template, Staff and threshold
    matches_head = template_matching(AvailableTemplates.ClosedNotehead, temp_staff, threshold)

    # do same for note flags
    template_flag = Template('1flag', 'images/templates/flag.png')
    matches_flag = template_matching(template_flag, temp_staff, threshold)
    
    # do a lot of template matching here to create all objects

    # first find the clefs, keys and time notations
    # next, find the staff/measure lines
    # next create measures, adding the clef, key and time to each measure (measure inherits from most close to its left)
    
    # normally, do some measure-line recognition, probably with template matching
    measure_locs = [297,806,1212,1617,1952] # for now manual locations
    measures = []
    for i in range(1,len(measure_locs)):
        measures.append(Staff_measure(temp_staff, i, measure_locs[i-1], measure_locs[i]))

    # add clefs, keys and timing to measures
    
    # create fake clef for testing
    blank_image = np.zeros([50,50,3],dtype=np.uint8)
    clef_template = Template('G',blank_image)
    temp_clef = Clef(measure_locs[0]+5,100,clef_template)
    
    # create fake flats for testing
    acc_template = Template('flat',blank_image)
    temp_acc_group = [Accidental(measure_locs[0]+15,temp_staff.lines[8][1],acc_template),Accidental(measure_locs[0]+20,temp_staff.lines[9][1],acc_template)]
    for acc in temp_acc_group:
        acc.find_note(measures[0])
    temp_key = Key(temp_acc_group)
    
    # create fake time signature for testing
    time_template = Template('3/4',blank_image)
    temp_time = Time(measure_locs[0]+30, 100, time_template)
    
    # We have 2 options for assigning the 'voortekens'
    # for meas in measure:
        # add clef, key and time
    #OF
    # for c in clefs:
        # add to corresponding measures
        
    # for now we use first option
    for meas in measures:
        meas.set_clef(temp_clef.type)
        meas.set_key(temp_key.key)
        meas.set_time(temp_time)
    
    # turn the found head symbols into objects and add corresponding information
    head_objects = []
    for head in matches_head:  # for each note head location found with template matching:
        head_obj = Head(head[0], head[1], template_head)  # turn into object
        head_obj.set_pitch(temp_staff)  # determine the pitch based on the Staff line locations
        if head_obj.pitch == 'Error': continue
        temp_measure = find_measure(measures,head_obj.x)
        # also here, first determine its corresponding measure, and use that to set the note
        # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
        head_obj.set_note(temp_measure)
        head_obj.set_key(temp_key)
        head_objects.append(head_obj)

    # find all vertical lines in the Staff object and assume to be note stems
    # vertical lines that are not stems are most likely not connected to note heads and thus will be ignored
    stem_objects = find_stems(temp_staff)
    
    # turn the found flag symbols into objects
    flag_objects = []
    for flag in matches_flag:
        flag_obj = Flag(flag[0], flag[1], template_flag)
        flag_objects.append(flag_obj)
    
    # takes all noteheads, stems and flags and the Staff object to determine full notes
    # in future also should take accidentals, dots, connection ties, etc.
    notes = build_notes(head_objects, stem_objects, flag_objects, temp_staff)

    # sort notes by x, and thus by time (later add rests first)
    notes.sort(key=lambda x: x.x)

    # select only notes for first measure (should later be done for each measure and maybe add list to the measure)
    m1_notes = [note for note in notes if note.x<measures[0].end]
    
    # even voor opvangen van het niet herkennen van beams:
    for note in m1_notes:
        if note.durname == "quarter":
            note.update_duration("eighth", int(note.duration/2))

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
    tree.write("mxml/filename.xml")


    # future: also use those grouping-staffs-symbols to determine whether next part in musicXML needs staff+=1 or measure_nr+=1


if __name__ == "__main__":
    main()
