import cv2 as cv

#from denoise.denoise import denoise
#from template_matching.template_matching import template_matching

from staffs.seperate_staffs import seperate_staffs
from staffs.staff_objects import Staff, Staff_measure#, Bar_line, split_measures
from notes.note_objects import Template, Head#, Stem #, Flag, Rest, Accidental, Dots, Relation
from notes.build_notes_objects import find_stems, build_notes
from template_matching.template_matching_mich import template_matching_mich

def main():
#    input = "INPUT IMAGE"
    input = 'images/Fmttm.png'
    
#    denoised_image = denoise(input) # returnt een binary image, maar de volgende functies hebben een rgb of grayscale image nodig om goed te werken
    #------------------------------------------------
    staff_imgs = seperate_staffs(cv.imread(input)) # seperate full sheet music into an image for each staff (input=rgb (grayscale also possible with slight adjustment in function))
    
    staffs = []
    for s in staff_imgs:
        staffs.append(Staff(s)) # create list of Staff objects, by creating Staff objects of the staff images
    
    temp_staff = staffs[0] # do only for first staff while testing
        
    threshold = 0.8 # threshold for template matching
    
    template_head = Template('closed head','images/head-filled.png') # create a Template object with object name and image filename
    matches_head = template_matching_mich(template_head,temp_staff,threshold) # do template matching with the Template, Staff and threshold
    
    # do a lot of template matching here to create all objects
    
    # first find the clefs, keys and time notations
    # next, find the staff/measure lines
    # next create measures, adding the clef, key and time to each measure (measure inherits from most close to its left)
    
    temp_measure = Staff_measure(temp_staff,0,0,temp_staff.image.shape[0]) # create a temporary Staff_measure object for testing (normally based on template matching with staffline templates)

    head_objects = []
    for head in matches_head: # for each note head location found with template matching:
        head_obj = Head(head[0],head[1],template_head) # turn into object
        head_obj.set_pitch(temp_staff) # determine the pitch based on the Staff line locations
        
        # also here, first determine its corresponding measure, and use that to set the note
        head_obj.set_note(temp_measure) # Use the Staff_measure object to determine the note name corresponding to the y-location of the note
        head_objects.append(head_obj) 
    
    stem_objects = find_stems(temp_staff) # find all vertical lines in the Staff object (function calls Staff.image)
    
    notes = build_notes(head_objects, stem_objects, [], temp_staff) # takes all noteheads, stems and flags and the Staff object to determine full notes
    
    for note in notes:
        print('%s%d'%(note.note,note.octave)) # for each Note object, print the note name and octave
        print(note.duration/temp_measure.divisions) # print the count of the note (where a quarter note = 1 count)
        print('\n')
        
    # next, use accidentals, dots and ties to update the accidental and time values
    
    # at end of staff, write to musicXML file
    # use x-locations to determine order of notes (and where to use <chord\>)
    # also use those grouping-staffs-symbols to determine whether next part in musicXML needs staff+=1 or measure_nr+=1
    
    
    #------------------------------------------------
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
