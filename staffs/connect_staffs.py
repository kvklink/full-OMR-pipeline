# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 12:32:29 2020

@author: super
"""
import cv2
import math
from utils.util import imshow

def connect_staffs(img, staffs):
    # needed: start and end locations of each staff
    staff_height = staffs[0].dist*4
    staff_tops = [s.top for s in staffs]
    staff_bottom = [s.bottom for s in staffs]
    staff_start = [s.x for s in staffs]
    
    img_struct_ver = img.copy()
    ver_size = int(img.shape[0] / 15)
    ver_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_size))
    img_struct_ver2 = cv2.dilate(img_struct_ver, ver_struct, 1)
    img_struct_ver2 = cv2.erode(img_struct_ver2, ver_struct, 1)

    gray_ver = cv2.cvtColor(img_struct_ver2, cv2.COLOR_BGR2GRAY)
    (thresh_ver, im_bw_ver) = cv2.threshold(gray_ver, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    img_canny_ver = im_bw_ver.copy()
    gray2_ver = cv2.cvtColor(img_canny_ver, cv2.COLOR_GRAY2BGR)

    edges2_ver = cv2.Canny(gray2_ver, 100, 200)

    lines2_ver = cv2.HoughLinesP(edges2_ver, 1, math.pi, 1, None, staff_height*2,
                                 10)  # edges, rho, theta, threshold, --, minlinelen, maxlinegap

#    # for show------
#    imcopy = img.copy()
#    for linearr in lines2_ver:
#        line = linearr[0]
#        cv2.line(imcopy, (line[0],line[1]),(line[2],line[3]),(0,0,255),2)
#    for t, b, x in zip(staff_tops, staff_bottom, staff_start):
#        cv2.circle(imcopy, (x, t), 1, (255, 0, 0), 3)
#        cv2.circle(imcopy, (x, b), 1, (0, 255, 0), 3)
#    imshow('vertical lines', imcopy)
#    # --------

    connected = []
    for linearr in lines2_ver:
        topstaff = bottomstaff = float('NaN')
        line = linearr[0]
        top = (line[2], line[3])
        bottom = (line[0], line[1])
        for i, (t, b, x) in enumerate(zip(staff_tops, staff_bottom, staff_start)):
            if t <= top[1] <= b and abs(x - top[0]) < staff_height:
                topstaff = i
            if t <= bottom[1] <= b and abs(x - bottom[0]) < staff_height:
                bottomstaff = i
        if not (math.isnan(topstaff) or math.isnan(bottomstaff)):
            connected.append((topstaff, bottomstaff))

    connected = list(set(connected))
    connected.sort(key=lambda x: x[0])
    
    for i, (s, e) in enumerate(connected):
        s_group = [*range(s, e+1, 1)]
        for j, g in enumerate(s_group):
            staffs[g].set_bar_nrs(i+1, j+1)