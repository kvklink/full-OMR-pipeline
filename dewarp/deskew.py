import sys
import math
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

from denoise.denoise import *
from utils.util import bgr_imshow, imshow

#====== PARAMS =====================================
# All Hough
RHO = 1                 # 1 pixel
THDEG = 90              # 90 degrees
THETA = np.pi * THDEG / 180
# Std Hough
THRES = 500
# Prob Hough
PTHRES = 600
MIN_PRC = 60
MAX_PRC = 5
#===================================================

# IO for testing
DIR = 'images/sheets/mscd-15/' #mscd-15/' #trombone/'
INPUT_PATH = DIR + 'input.png'
OUTPUT_PATH = DIR + 'deskewed_denoised.png'
SHOUGH_TITLE = f"shough ({RHO},{THDEG},{THRES})"
PHOUGH_TITLE = f"phough ({RHO},{THDEG},{PTHRES},{MIN_PRC}%,{MAX_PRC}%)"
SHOUGH_PATH = DIR + "rotate/" + SHOUGH_TITLE + ".png"
PHOUGH_PATH = DIR + "rotate/" + PHOUGH_TITLE + ".png"

def rotate(img, angle):
    nrows, ncols = img.shape 
    center = (ncols/2, nrows/2)
    mat = cv.getRotationMatrix2D(center, angle, 1)
    dst = cv.warpAffine(img, mat, (ncols, nrows), flags=cv.INTER_LINEAR)
    # bgr_imshow(f"Rotated {angle_deg} degrees", dst)
    return dst

'''Assumes a denoised grayscale image as input'''
def optimize(img):
    best_score = 0
    best_angle = 0
    for angle in np.arange(-5, 5, 0.01):
        img_rot = rotate(img, angle)
        sscore, pscore = hough_score(img_rot)
        score = pscore
        if score > best_score:
            best_score, best_angle = score, angle
    print("Winner winner chicken dinner")
    print(best_score)
    print(best_angle)
    # rotate img until optimal
    # optimality is tested by counting succesful hough 90deg line recognization
    return best_angle

def hough_score(img):
    ncols = img.shape[1]
    
    # Edge detection
    edgdt = True
    if edgdt:
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

    nlinesS = len(lines) if lines is not None else 0
    nlinesP = len(linesP) if linesP is not None else 0
    return nlinesS, nlinesP

'''Assumes a denoised grayscale image as input'''
def deskew(img):
    best_angle = optimize(img)
    deskewed = rotate(img, best_angle)
    return deskewed

if __name__ == "__main__":
    img = denoise(cv.imread(INPUT_PATH, cv.IMREAD_GRAYSCALE))
    deskewed = deskew(img)
    # best_angle = optimize(denoised) # = 0.62
    # deskewed = rotate(denoised, best_angle)
    # hough_score(deskewed)
    cv.imwrite(OUTPUT_PATH, deskewed)