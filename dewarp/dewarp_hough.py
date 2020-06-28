"""
@file dewarp_hough.py
@brief This program demonstrates line finding with the Hough transform. Eventual goal is to dewarp the music sheet image.
"""
import sys
import math
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

from denoise.denoise import *
from utils.util import bgr_imshow

#====== PARAMS =====================================
DENOISE_FIRST = True
EDGEDET_FIRST = True
# All Hough
RHO = 1                 # 1 pixel
THDEG = 0.2              # 1 degree
THETA = np.pi * THDEG / 180
# Std Hough
THRES = 400 #250 #150
# Prob Hough
PTHRES = 300 #100 #20 #50
MIN_PRC = 60
# MIN_LEN = 100 #0.6 * ncols #500 #100 #50 #100 #50
MAX_PRC = 5
# MAX_GAP = 9 #0.05 * ncols #50 #10
#===================================================

# IO for testing
DIR = 'images/sheets/trombone-quality/' #mscd-15/' #trombone/'
INPUT_PATH = DIR + 'input.png'
SHOUGH_TITLE = f"shough ({RHO},{THDEG},{THRES}) [dnois={DENOISE_FIRST}, canny={EDGEDET_FIRST}]"
PHOUGH_TITLE = f"phough ({RHO},{THDEG},{PTHRES},{MIN_PRC}%,{MAX_PRC}%) [denos={DENOISE_FIRST}, canny={EDGEDET_FIRST}]"
SHOUGH_PATH = DIR + SHOUGH_TITLE + ".png"
PHOUGH_PATH = DIR + PHOUGH_TITLE + ".png"

def main():    
    # Retrieve source
    if DENOISE_FIRST:
        src = denoise(INPUT_PATH)
    else:
        src = cv.imread(INPUT_PATH, cv.IMREAD_GRAYSCALE)
    if src is None:
        print ('Error opening image!')
        return -1
    bgr_imshow("Source", src)
    ncols = src.shape[1]
    
    # TODO: Try dilate/erode before/after edge detction

    # Edge detection
    if EDGEDET_FIRST:
        dst = cv.Canny(src, 50, 200, None, 3)
        bgr_imshow("Edge detection", dst)
    else:
        dst = cv.bitwise_not(src) #cv.cvtColor(src, cv.COLOR_RGB2GRAY)

    # Copy edges to the images that will display the results in BGR
    cdst = cv.cvtColor(dst, cv.COLOR_GRAY2BGR)
    cdstP = np.copy(cdst)
    
    # Standard Hough    
    lines = cv.HoughLines(dst, RHO, THETA, THRES, None, 0, 0)
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
            pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
            cv.line(cdst, pt1, pt2, (0,0,255), thickness=1, lineType=cv.LINE_AA)
    bgr_imshow(SHOUGH_TITLE, cdst)
    cv.imwrite(SHOUGH_PATH, cdst)

    # Probabalistic Hough
    linesP = cv.HoughLinesP(dst, RHO, THETA, PTHRES, None, MIN_PRC * ncols / 100, MAX_PRC * ncols / 100)
    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[i][0]
            cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0,0,255), thickness=1, lineType=cv.LINE_AA)
    

    bgr_imshow(PHOUGH_TITLE, cdstP)
    cv.imwrite(PHOUGH_PATH, cdstP)
    
    cv.waitKey()
    return 0

if __name__ == "__main__":
    main()