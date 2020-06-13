# -*- coding: utf-8 -*-
"""
Created on Fri Jun 12 16:47:28 2020

@author: super
"""

import cv2
import math
from detect_stafflines import calc_y

pitch_list = ['G6','F6','E6','D6','C6','B6','A6','G5','F5','E5','D5','C5','B5','A5','G4','F4','E4','D4']

def find_pitch(x,y,dist,lines):
    line_vals = []
    for l in lines:
        line_vals.append(calc_y(l,x))
        
    if y<min(line_vals):
        print('too high: %d'%y)
        return('Error')
    elif y>max(line_vals):
        print('too low: %d'%y)
        return('Error')
    else:
        i=0
        found = False
        while found==False:
            i = i+1
            found = (y<line_vals[i])
        
        s = line_vals[i-1]
        e = line_vals[i]
        
        # use dist/4
        if y in range(int(e-dist/4)+1,e+1):
            pitch = line_vals.index(e)*2
        elif y in range(s,int(s+dist/4)):
            pitch = line_vals.index(s)*2
        else: pitch = line_vals.index(e)*2-1

    return pitch_list[pitch]

def set_pitch(heads,h_head,w_head):
    pitches = []
    for pt in heads:
        y = int(pt[1]+(h_head/2)-1)
        x = int(pt[0]+(w_head/2)-1)
        pitch = find_pitch(x,y)
        pitches.append(pitch)
        
    return pitches

def find_stems(img_bar):
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
    
    return lines2_ver

def build_notes(heads, w_head, h_head, stems, flags, w_flag, h_flag, dist):
    nd = int(dist/8)
    
    quarter = []
    
    for pt in heads:
        hx1, hy1 = pt
        hx2, hy2 = (hx1+w_head, hy1+h_head)
        
        for line in stems:
            sx1, sy1, sx2, sy2 = line[0]
            
            if sy1 in range(hy1,hy2+1) or sy2 in range(hy1,hy2+1):
                if sx1 in range(hx1-nd,hx2+nd+1) or sx2 in range(hx1-nd,hx2+nd+1):
                    xmin = min(sx1,sx2,hx1,hx2)
                    xmax = max(sx1,sx2,hx1,hx2)
                    ymin = min(sy1,sy2,hy1,hy2)
                    ymax = max(sy1,sy2,hy1,hy2)
                    
                    quarter.append(xmin,ymin,xmax,ymax)
    
    eighth = []
    
    for q in quarter:
        qx1, qy1, qx2, qy2 = q
        
        for f in flags:
            fx1, fy1 = f
            fx2, fy2 = (fx1+w_flag, fy1+h_flag)
            
            if fy1 in range(qy1,qy2+1) or fy2 in range(qy1,qy2+1):
                if fx1 in range(qx1-nd,qx2+nd+1) or fx2 in range(qx1-nd,qx2+nd+1):
                    xmin = min(fx1,fx2,qx1,qx2)
                    xmax = max(fx1,fx2,qx1,qx2)
                    ymin = min(fy1,fy2,qy1,qy2)
                    ymax = max(fy1,fy2,qy1,qy2)
                    
                    eighth.append(xmin,ymin,xmax,ymax)
                    
    # somewhere here remove quarter notes that are now eighth notes
    # also detect full, half and sixteenth notes
    
    notes = {'full':[], 'half':[], 'quarter':quarter, 'eighth':eighth, 'sixteenth':[]}
    
    return notes
    
    
    
    
    