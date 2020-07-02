# -*- coding: utf-8 -*-
"""
Created on Fri Jun 12 16:35:16 2020

@author: super
"""
from typing import List

import cv2
import numpy as np


def separate_staffs(img) -> List:
    rows, cols = img.shape[:2]

    img_struct = img.copy()
    #    gray = img.copy()

    gray = cv2.cvtColor(img_struct, cv2.COLOR_BGR2GRAY)
    (thresh, im_bw) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    erode_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
    dilate_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))

    step1 = cv2.erode(im_bw, erode_struct, 1)
    step2 = cv2.dilate(step1, dilate_struct, 1)
    im_inv = cv2.bitwise_not(step2)

    img_row_sum: List = np.sum(im_inv, axis=1).tolist()

    threshold = 0.5
    for i, r in enumerate(img_row_sum):
        perc = r / (255 * im_inv.shape[1])
        img_row_sum[i] = perc

    start = []
    end = []
    full = []
    for i, val in enumerate(img_row_sum):
        if i == 0:
            continue
        if val >= threshold > img_row_sum[i - 1]:
            start.append(i)
            full.append(i)
        elif val < threshold < img_row_sum[i - 1]:
            end.append(i)
            full.append(i)


    if end[0] < start[0]:
        del end[0]
    if start[-1] > end[-1]:
        start.pop()

    xs = []
    for s, e in zip(start, end):
        bar = im_inv[s:e, 0:im_inv.shape[1]]
        img_col_sum: List = np.sum(bar, axis=0).tolist()

        threshold = 0.8
        for i, c in enumerate(img_col_sum):
            perc = c / (255 * bar.shape[0])
            img_col_sum[i] = perc

        i = int(bar.shape[1]/2)
        while img_col_sum[i] > 0.5:
            i -= 1
        xs.append(i)

#    imcopy = cv2.cvtColor(im_inv, cv2.COLOR_GRAY2BGR)
#    colours = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]
#    for i in range(len(start)):
#        s = start[i]
#        e = end[i]
#        x = xs[i]
#        cv2.line(imcopy, (x, s), (cols, s), colours[i], 2)
#        cv2.line(imcopy, (x, e), (cols, e), colours[i], 2)
#
#    img_small = cv2.resize(imcopy, (0,0), fx=0.5, fy=0.5)
#    cv2.imshow('staff start', img_small)

    cut = []
    for i, val in enumerate(full):
        if i == 0:
            if val in start and full[i + 2] in start:
                dist = full[i + 2] - val
                cutloc_s = val - dist
                cut.append([max(cutloc_s, 0), full[i + 2]])
        elif i == len(full) - 2 and val in start and full[i - 1] in end and full[i + 1] in end:
            dist = full[i + 1] - full[i - 1]
            cutloc_e = full[i + 1] + dist
            cut.append([full[i - 1], min(cutloc_e, len(img_row_sum) - 1)])
        elif i == len(full) - 1:
            break
        elif val in start and full[i - 1] in end and full[i + 2] in start:
            cut.append([full[i - 1], full[i + 2]])

    staffs = []
    for i in range(len(cut)):
        crop1 = img[cut[i][0]:cut[i][1], 0:img.shape[1]]
        staffs.append((crop1, (start[i],end[i]), xs[i])) #0 nog veranderen in x waarde start van staff

    return staffs
