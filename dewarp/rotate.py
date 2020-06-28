import sys
import math
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

from denoise.denoise import *
from utils.util import bgr_imshow, imshow

#====== PARAMS =====================================
DENOISE_FIRST = True
EDGEDET_FIRST = True
# All Hough
RHO = 1                 # 1 pixel
THDEG = 90              # 1 degree
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

def rotate(img, angle_deg):
    angle = np.pi * angle_deg / 180
    nrows, ncols = img.shape 
    center = (nrows/2, ncols/2)
    mat = cv.getRotationMatrix2D(center, angle, 1)
    dst = cv.warpAffine(img, mat, (ncols, nrows))
    # bgr_imshow(f"Rotated {angle_deg} degrees", dst)
    return dst

def optimize(img):
    # Retrieve source
    if DENOISE_FIRST:
        img = denoise(img)
        # bgr_imshow("Source", img)

    best_score = 0
    best_angle = 0
    for angle in np.arange(0.0, 10, 0.1):
        img_rot = rotate(img, angle)
        score = hough_score(img_rot)[1]
        print(angle, score)
        if score > best_score:
            best_score, best_angle = score, angle
    print("Winner winner chicken dinner")
    print(best_score)
    print(best_angle)

    # rotate img until optimal
    # optimality is tested by counting succesful hough 90deg line recognization
    return img

def hough_score(img):
    ncols = img.shape[1]
    
    # Edge detection
    if EDGEDET_FIRST:
        dst = cv.Canny(img, 50, 200, None, 3)
        # bgr_imshow("Edge detection", dst)
    else:
        dst = cv.bitwise_not(img)
    cdst = cv.cvtColor(dst, cv.COLOR_GRAY2BGR)
    cdstP = np.copy(cdst)
    
    # Standard Hough    
    lines = cv.HoughLines(dst, RHO, THETA, THRES, None, 0, 0)
    if lines is not None:
        for i in range(0, len(lines)):
            line_len = ncols * 1.5
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + line_len*(-b)), int(y0 + line_len*(a)))
            pt2 = (int(x0 - line_len*(-b)), int(y0 - line_len*(a)))
            cv.line(cdst, pt1, pt2, (0,0,255), thickness=1, lineType=cv.LINE_AA)
    # bgr_imshow(SHOUGH_TITLE, cdst)
    # cv.imwrite(SHOUGH_PATH, cdst)

    # Probabilistic Hough
    linesP = cv.HoughLinesP(dst, RHO, THETA, PTHRES, None, MIN_PRC * ncols / 100, MAX_PRC * ncols / 100)
    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[i][0]
            cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0,0,255), thickness=1, lineType=cv.LINE_AA)
    
    # bgr_imshow(PHOUGH_TITLE, cdstP)
    # cv.imwrite(PHOUGH_PATH, cdstP)
    
    cv.waitKey()
    no_lines = 0
    return len(lines), len(linesP)

if __name__ == "__main__":
    img = cv.imread(INPUT_PATH, cv.IMREAD_GRAYSCALE)
    rotate(img, 7.1)
    optimize(img)