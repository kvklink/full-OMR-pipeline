import cv2 as cv

#from denoise.denoise import denoise
#from template_matching.template_matching import template_matching

from staffs.seperate_staffs import seperate_staffs
from staffs.staff_objects import Staff #, Staff_measure, Bar_line, split_measures
from notes.note_objects import Template, Head#, Stem #, Flag, Rest, Accidental, Dots, Relation
from notes.build_notes_objects import find_stems, build_notes
from template_matching.template_matching_mich import template_matching_mich

def main():
#    input = "INPUT IMAGE"
    input = 'images/Fmttm.png'
    
#    denoised_image = denoise(input) # returnt een binary image, maar de volgende functies hebben een rgb of grayscale image nodig om goed te werken
    #------------------------------------------------
    staff_imgs = seperate_staffs(cv.imread(input))
    
    staffs = []
    for s in staff_imgs:
        staffs.append(Staff(s))
        
    threshold = 0.8
    
    temp_staff = staffs[0] #do only for first image in testing
    
    template_head = Template('closed head','images/head-filled.png')
    matches_head = template_matching_mich(template_head,temp_staff,threshold)
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
