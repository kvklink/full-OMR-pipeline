# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 16:52:35 2020

@author: super
"""

import cv2
import math
from notes.note_objects import Stem, Note

def find_stems(staff):
    img_bar = staff.image
    img_struct_ver = img_bar.copy()
    ver_size = int(img_bar.shape[0]/15)
    ver_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1,ver_size))
    img_struct_ver2 = cv2.dilate(img_struct_ver, ver_struct, 1)
    img_struct_ver2 = cv2.erode(img_struct_ver2, ver_struct, 1)
    
    gray_ver = cv2.cvtColor(img_struct_ver2, cv2.COLOR_BGR2GRAY)
    (thresh_ver, im_bw_ver) = cv2.threshold(gray_ver, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    img_canny_ver = im_bw_ver.copy()
    gray2_ver = cv2.cvtColor(img_canny_ver, cv2.COLOR_GRAY2BGR)
    
    edges2_ver = cv2.Canny(gray2_ver, 100,200)
    
    lines2_ver = cv2.HoughLinesP(edges2_ver, 1, math.pi, 1, None, 10, 10) #edges, rho, theta, threshold, --, minlinelen, maxlinegap
    
    stem_list = []
    for line in lines2_ver:
        l = line[0]
        stem_list.append(Stem(l[0],l[1],l[2],l[3]))
    
    
    return stem_list


def build_notes(heads, stems, flags, staff):
    dist = staff.dist
    nd = int(dist/8)
    
    notes = []
    
    for head in heads:
        hx1, hy1 = head.x, head.y
        hx2, hy2 = (hx1+head.w, hy1+head.h)
        
        for stem in stems:
            sx1, sy1 = stem.x, stem.y
            sx2, sy2 = (sx1+stem.w, sy1+stem.h)
            
            if sy1 in range(hy1,hy2+1) or sy2 in range(hy1,hy2+1):
                if sx1 in range(hx1-nd,hx2+nd+1) or sx2 in range(hx1-nd,hx2+nd+1):
                    xmin = min(sx1,sx2,hx1,hx2)
                    xmax = max(sx1,sx2,hx1,hx2)
                    ymin = min(sy1,sy2,hy1,hy2)
                    ymax = max(sy1,sy2,hy1,hy2)
                    
                    notes.append(Note(head,1/4,(xmin,ymin,xmax,ymax)))
    
    for note in notes:
        nx1, ny1 = note.x, note.y
        nx2, ny2 = (nx1+note.w, ny1+note.h)
        
        for flag in flags:
            fx1, fy1 = flag.x, flag.y
            fx2, fy2 = (fx1+flag.w, fy1+flag.h)
            
            if fy1 in range(ny1,ny2+1) or fy2 in range(ny1,ny2+1):
                if fx1 in range(nx1-nd,nx2+nd+1) or fx2 in range(nx1-nd,nx2+nd+1):
                    xmin = min(fx1,fx2,nx1,nx2)
                    xmax = max(fx1,fx2,nx1,nx2)
                    ymin = min(fy1,fy2,ny1,ny2)
                    ymax = max(fy1,fy2,ny1,ny2)
                    
                    new_loc = (xmin,ymin,xmax,ymax)
                    
                    note.update_location(new_loc)
                    note.update_duration(note.duration/2)
                    
    # somewhere here remove quarter notes that are now eighth notes
    # also detect full, half and sixteenth notes
        
    return notes