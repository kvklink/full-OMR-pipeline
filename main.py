import cv2 as cv
import numpy as np

from notes.build_notes_objects import find_stems, build_notes
from notes.note_objects import Template, Head, Stem, Flag, Rest, Accidental, Dots, Relation
from staffs.seperate_staffs import seperate_staffs
from staffs.staff_objects import Staff, Staff_measure, find_measure, Clef, Key, Time, Bar_line, split_measures
from template_matching.template_matching import template_matching


# from denoise.denoise import denoise
# from template_matching.template_matching import template_matching

def main():
    input = 'images/sheets/Fmttm.png'

    # returnt een binary image, maar de volgende functies hebben een rgb of grayscale image nodig om goed te werken
    #    denoised_image = denoise(input)
    # ------------------------------------------------
    # seperate full sheet music into an image for each staff
    # (input=rgb (grayscale also possible with slight adjustment in function))
    staff_imgs = seperate_staffs(cv.imread(input))

    staffs = []
    for s in staff_imgs:
        staffs.append(Staff(s))  # create list of Staff objects, by creating Staff objects of the staff images

    temp_staff = staffs[0]  # do only for first staff while testing

    threshold = 0.8  # threshold for template matching

    # create a Template object with object name and image filename
    template_head = Template('closed head', 'images/templates/head-filled.png')
    # do template matching with the Template, Staff and threshold
    matches_head = template_matching(template_head, temp_staff, threshold)

    # do a lot of template matching here to create all objects

    # first find the clefs, keys and time notations
    # next, find the staff/measure lines
    # next create measures, adding the clef, key and time to each measure (measure inherits from most close to its left)

    # create a temporary Staff_measure object for testing (normally based on template matching with staffline templates)
#    temp_measure = Staff_measure(temp_staff, 0, 0, temp_staff.image.shape[0])
    
    #----------
    measure_locs = [297,806,1212,1617,1952]
    #create staff measure: Staff_measure(staff, nr, start, end)
    measures = []
    for i in range(1,len(measure_locs)):
        measures.append(Staff_measure(temp_staff, i, measure_locs[i-1], measure_locs[i]))
    #----------
    
    # add clefs, keys and timing to measures
    
    blank_image = np.zeros([50,50,3],dtype=np.uint8)
    clef_template = Template('G',blank_image)
    temp_clef = Clef(measure_locs[0]+5,100,clef_template)
    
    acc_template = Template('flat',blank_image)
    temp_acc_group = [Accidental(measure_locs[0]+15,temp_staff.lines[8][1],acc_template),Accidental(measure_locs[0]+20,temp_staff.lines[9][1],acc_template)]
    for acc in temp_acc_group:
        acc.find_note(measures[0])
    temp_key = Key(temp_acc_group)
    
    time_template = Template('common',blank_image)
    temp_time = Time(measure_locs[0]+30, 100, time_template)
    
    # for meas in measure:
        # add clef, key and time
        
    #OF
    
    # for c in clefs:
        # add to corresponding measures
        
    for meas in measures:
        meas.set_clef(temp_clef.type)
        meas.set_key(temp_key.key)
        meas.set_time(temp_time)
    

    head_objects = []
    for head in matches_head:  # for each note head location found with template matching:
        head_obj = Head(head[0], head[1], template_head)  # turn into object
        head_obj.set_pitch(temp_staff)  # determine the pitch based on the Staff line locations

        temp_measure = find_measure(measures,head_obj.x)
        # also here, first determine its corresponding measure, and use that to set the note
        # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
        head_obj.set_note(temp_measure)
        head_obj.set_key(temp_key)
        head_objects.append(head_obj)

        # find all vertical lines in the Staff object (function calls Staff.image)
    stem_objects = find_stems(temp_staff)
    
    # takes all noteheads, stems and flags and the Staff object to determine full notes
    notes = build_notes(head_objects, stem_objects, [], temp_staff)

    for note in notes:
        # for each Note object, print the note name and octave
        print(f'{note.note} {note.octave} {note.accidental}')
        # print the count of the note (where a quarter note = 1 count)
        print(note.duration / temp_measure.divisions)
        print('\n')

    # next, use accidentals, dots and ties to update the accidental and time values

    # at end of staff, write to musicXML file
    # use x-locations to determine order of notes (and where to use <chord\>)
    # also use those grouping-staffs-symbols to determine whether next part in musicXML needs staff+=1 or measure_nr+=1

    # ------------------------------------------------


#    template_matched_image = template_matching(denoised_image)
#    
#    print(template_matched_image)
#
#    cv.namedWindow('output', cv.WINDOW_NORMAL)
#    cv.resizeWindow('output', 1100, 1100)
#    cv.imshow('output', template_matching('/Users/kyle/Desktop/input.jpeg'))
#    cv.waitKey(0)
#    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
