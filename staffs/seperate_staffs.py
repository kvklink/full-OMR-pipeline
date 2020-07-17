# -*- coding: utf-8 -*-
"""
Created on Fri Jun 12 16:35:16 2020

@author: super
"""
from typing import List

import cv2
import numpy as np
from utils.util import imshow


def separate_staffs(img) -> List:
    rows, cols = img.shape[:2]

    img_struct = img.copy()
    gray = cv2.cvtColor(img_struct, cv2.COLOR_BGR2GRAY)
    
    (thresh, im_bw) = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)# | cv2.THRESH_OTSU)

    erode_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
    dilate_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))

    step1 = cv2.erode(im_bw, erode_struct, 1)
    step2 = cv2.dilate(step1, dilate_struct, 1)
    im_inv = cv2.bitwise_not(step2)

    imshow('structed', im_inv)

    img_row_sum: List = np.sum(im_inv, axis=1).tolist()

    threshold = 0.6
    for i, r in enumerate(img_row_sum):
        perc = r / (255 * im_inv.shape[1])
        img_row_sum[i] = perc

    start = []
    end = []
    for i, val in enumerate(img_row_sum):
        if i == 0:
            continue
        if val >= threshold > img_row_sum[i - 1]:
            start.append(i)
        elif val < threshold < img_row_sum[i - 1]:
            end.append(i)


    if end[0] < start[0]:
        del end[0]
    if start[-1] > end[-1]:
        start.pop()

    xs = []
    xe = []
    for s, e in zip(start, end):
        bar = im_inv[s:e, 0:im_inv.shape[1]]
        img_col_sum: List = np.sum(bar, axis=0).tolist()

        for i, c in enumerate(img_col_sum):
            perc = c / (255 * bar.shape[0])
            img_col_sum[i] = perc

        i = int(bar.shape[1]/2)
        while img_col_sum[i] > 0.5 and i > 0:
            i -= 1
        xs.append(i)
        
        j = int(bar.shape[1]/2)
        while img_col_sum[j] > 0.5 and j < len(img_col_sum)-1:
            j += 1
        xe.append(j)

    imcopy = img.copy()
    colours = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]
    for i in range(len(start)):
        s = start[i]
        e = end[i]
        x = xs[i]
        cv2.line(imcopy, (x, s), (cols, s), colours[i%4], 1)
        cv2.line(imcopy, (x, e), (cols, e), colours[i%4], 1)
#    imshow('staff boundaries', imcopy)

    cut = []
    for i in range(min(len(start), len(end))):
        if i == 0:
            dist = start[i+1] - start[i]
            cutloc = start[i] - dist
            cut.append([max(cutloc, 0), start[i+1]])
        elif i == min(len(start), len(end)) - 1:
            dist = end[i] - end[i-1]
            cutloc = end[i] + dist
            cut.append([end[i-1], min(cutloc, len(img_row_sum) - 1)])
        else:
            cut.append([end[i-1], start[i+1]])
    
    imcopy = img.copy()#cv2.cvtColor(im_inv, cv2.COLOR_GRAY2BGR)
    colours = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]
    for i in range(len(cut)):
        s = cut[i][0]
        e = cut[i][1]
        cv2.line(imcopy, (0, s), (cols, s), colours[i%4], 1)
        cv2.line(imcopy, (0, e), (cols, e), colours[i%4], 1)
#    imshow('cut lines', imcopy)

    staffs = []
    for i in range(len(cut)):
        crop1 = img[cut[i][0]:cut[i][1], 0:img.shape[1]]
        staffs.append((crop1, (start[i],end[i]), (cut[i][0], cut[i][1]), (xs[i], xe[i])))

    return staffs
