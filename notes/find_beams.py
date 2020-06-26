# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 12:46:16 2020

@author: super
"""
import cv2
import math
import numpy as np
from notes.note_objects import Beam

def find_beams(staff):
    img = staff.image.copy()
    ver_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1,5))
    img_struct_ver = cv2.dilate(img, ver_struct, 1)
#    cv2.imshow('trans image ver', img_struct_ver)
    
    hor_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (25,1))
    img_struct_hor = cv2.dilate(img_struct_ver, hor_struct, 1)
    
    img_erode = cv2.erode(img_struct_hor, hor_struct, 1)
    img_erode2 = cv2.erode(img_erode, ver_struct, 1)

    
    # line detection
    gray = cv2.cvtColor(img_erode2, cv2.COLOR_BGR2GRAY)
    (thresh, img_bw) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    gray2 = cv2.cvtColor(img_bw, cv2.COLOR_GRAY2BGR)
    edges2 = cv2.Canny(gray2, 100,200)
    lines = cv2.HoughLinesP(edges2, 1, math.pi/180, 1, None, 10, 1)
    
    # corner detection
    gray2 = np.float32(gray)
    #image, blockSize (size neighbourhood considered), ksize (aperture for Sobel), k (free param)
    dest = cv2.cornerHarris(gray2, 2, 5, 0.07)
    # make corner indicators bigger
    dest2 = cv2.dilate(dest, None)
    # take only corners above threshold 0.01*max
    img_erode2[dest2 > 0.01 * dest2.max()] = [0, 0, 255]
    
    # locations indicated in dest:
    corners = dest.copy()
    corners[dest > 0.01 *dest.max()] = 255
    corners[dest < 0.01 *dest.max()] = 0
    
    result = np.where(corners == 255)
    
    coords = []
    for r,c in zip(result[0],result[1]):
        coords.append([r,c])

    delete_ind = []
    for i in range(len(coords)):
        for j in range(i+1,len(coords)):
            if abs(coords[i][0]-coords[j][0])<6 and abs(coords[i][1]-coords[j][1])<6:
                if j not in delete_ind:
                    delete_ind.append(j)
                    
    unique_coords = []
    for i in range(len(coords)):
        if i not in delete_ind:
            unique_coords.append(coords[i])

    def pythagoras(p1,p2):
        dist = math.sqrt(abs(p1[0]-p2[0])**2+abs(p1[1]-p2[1])**2)
        return dist
    
    lines2 = []
    for line in lines:
        l = line[0]
        length = math.sqrt(abs(l[0]-l[2])**2+abs(l[1]-l[3])**2)
        if length>10:
            lines2.append(l)
    
    lines2 = sorted(lines2, key=lambda x: x[0])
    
    beams = []
    # for each line, find closest corners to represent actual line endings
    for line in lines2:
        p1 = [line[1], line[0]]
        p2 = [line[3], line[2]]
        l_left, l_right = sorted([p1,p2], key=lambda x: x[1])
        
        best_dict_l = {'closest':(float('NaN'),[]),'backup':(float('NaN'),[])}
        best_dict_r = {'closest':(float('NaN'),[]),'backup':(float('NaN'),[])}
        
        for i in range(len(unique_coords)):
            corner = unique_coords[i]
            if corner[1]<=l_left[1]+5:
                # calc dist and if smaller than current, substitute
                curr_dist_l = pythagoras(l_left, corner)
                if math.isnan(best_dict_l['closest'][0]) or curr_dist_l < best_dict_l['closest'][0]:
                    best_dict_l['backup'] = best_dict_l['closest']
                    best_dict_l['closest'] = (curr_dist_l, corner)
                elif math.isnan(best_dict_l['backup'][0]) or curr_dist_l < best_dict_l['backup'][0]:
                    best_dict_l['backup'] = (curr_dist_l, corner)
                
            if corner[1]>=l_right[1]-5:
                curr_dist_r = pythagoras(l_right, corner)
                if math.isnan(best_dict_r['closest'][0]) or curr_dist_r < best_dict_r['closest'][0]:
                    best_dict_r['backup'] = best_dict_r['closest']
                    best_dict_r['closest'] = (curr_dist_r, corner)
                elif math.isnan(best_dict_r['backup'][0]) or curr_dist_r < best_dict_r['backup'][0]:
                    best_dict_r['backup'] = (curr_dist_r, corner)
             
        if best_dict_l['closest'][1] == best_dict_r['closest'][1]:
            if best_dict_l['closest'][0] < best_dict_r['closest'][0]:
                beams.append([best_dict_l['closest'][1], best_dict_r['backup'][1]])
            else:
                beams.append([best_dict_l['backup'][1], best_dict_r['closest'][1]])
        else:
            beams.append([best_dict_l['closest'][1], best_dict_r['closest'][1]])

    beam_tuples = []
    for beam in beams:
        beam_tup = (beam[0][0],beam[0][1],beam[1][0],beam[1][1])
        if beam_tup not in beam_tuples:
            beam_tuples.append(beam_tup)
        
#    for beam in beam_tuples:
#        pt1 = (beam[1],beam[0])
#        pt2 = (beam[3],beam[2])
#        cv2.line(img, pt1, pt2, (0,0,255), 2)
#    
#    cv2.imshow('beams', img)
    
    beam_objects = []
    for b in beam_tuples:
        beam_objects.append(Beam(b[1],b[0],b[3],b[2],'single_beam'))
            
    return beam_objects
    
    