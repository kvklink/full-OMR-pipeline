# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 18:01:59 2020

@author: super
"""

import cv2
import numpy as np

def template_matching(template, staff, threshold):
    img_gray = cv2.cvtColor(staff.image, cv2.COLOR_BGR2GRAY)
    results = cv2.matchTemplate(img_gray, template.image, cv2.TM_CCOEFF_NORMED)
    locations = np.where(results >= threshold)
    
    matches = []
    for pt in zip(*locations[::-1]):
        matches.append([pt[0],pt[1]])
        
    matches.sort()
    remove_match = []
    for i,pt in enumerate(matches):
        if i in remove_match: continue
        for j in range(i+1,len(matches)):
            pt2 = matches[j]
            if pt2[0] in range(pt[0]-4,pt[0]+4) and pt2[1] in range(pt[1]-3,pt[1]+3):
                remove_match.append(j)
                
    unique_matches = []
    for i in range(len(matches)):
        if i not in remove_match:
            unique_matches.append(matches[i])

    return unique_matches