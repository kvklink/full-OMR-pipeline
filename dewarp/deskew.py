import math

import numpy as np

from denoise.denoise import *
from utils.util import *

# ====== PARAMS =====================================
# All Hough
RHO = 1         # 1 pixel
THDEG = 90      # 90 degrees
# Std Hough
THRES = 500
# Prob Hough
PTHRES = 600
MIN_PRC = 60
MAX_PRC = 5
# ===================================================

# IO for testing
DIR = 'images/sheets/mscd-15/'  # mscd-15/' #trombone/'
INPUT_PATH = DIR + 'input.png'
OUTPUT_PATH = DIR + 'dewarped_denoised.png'


def rotate(img, angle, is_rgb=False):
    if is_rgb:
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    nrows, ncols = img.shape
    center = (ncols / 2, nrows / 2)
    mat = cv.getRotationMatrix2D(center, angle, 1)
    dst = cv.warpAffine(img, mat, (ncols, nrows), flags=cv.INTER_LINEAR)
    # bgr_imshow(f"Rotated {angle_deg} degrees", dst)
    if is_rgb:
        dst = cv.cvtColor(dst, cv.COLOR_GRAY2RGB)
    return dst


'''Assumes a denoised grayscale image as input'''
def optimize(img):
    best_score = 0
    best_angle = 0
    for angle in np.arange(-5, 5, 0.01):
        img_rot = rotate(img, angle, is_rgb=False)
        sscore, pscore = hough_scores(img_rot)
        score = pscore
        if score > best_score:
            best_score, best_angle = score, angle
    print("Winner winner chicken dinner")
    print(best_score)
    print(best_angle)
    # rotate img until optimal
    # optimality is tested by counting succesful hough 90deg line recognization
    return best_angle


def hough_scores(img):
    slines, _ = std_houghlines(img)
    plines = prb_houghlines(img)
    n_slines = len(slines) if slines is not None else 0
    n_plines = len(plines) if plines is not None else 0
    return n_slines, n_plines


def detect_edges(img, show=False):
    gray = cv.Canny(img, 50, 200, None, 3)
    if show:
        bgr_imshow("Edge detection", gray)
    return gray


def std_houghlines(img, rho=RHO, theta_deg=THDEG, threshold=THRES,
                    show=False, save=False):
    gray_img = detect_edges(img)
    bgr_img = cv.cvtColor(gray_img, cv.COLOR_GRAY2BGR)
    width = gray_img.shape[1]
    theta = to_radians(theta_deg)

    lines = cv.HoughLines(gray_img, rho, theta, threshold, None, 0, 0)

    coords = []
    if lines is not None:
        for i in range(0, len(lines)):
            line_len = width * 1.5
            line_rho = lines[i][0][0]
            line_theta = lines[i][0][1]
            a = math.cos(line_theta)
            b = math.sin(line_theta)
            x0 = a * line_rho
            y0 = b * line_rho
            pt1 = (int(x0 + line_len * (-b)), int(y0 + line_len * (a)))
            pt2 = (int(x0 - line_len * (-b)), int(y0 - line_len * (a)))
            coords.append((pt1, pt2))
            cv.line(bgr_img, pt1, pt2, (0, 0, 255), thickness=1,
                    lineType=cv.LINE_AA)

    title = f"shough ({rho},{theta_deg},{threshold})"
    if show:
        bgr_imshow(title, bgr_img)
    if save:
        path = DIR + "rotate/" + title + ".png"
        cv.imwrite(path, bgr_img)
    return lines, coords


def prb_houghlines(img, rho=RHO, theta_deg=THDEG, threshold=PTHRES,
                    min_line_prc=MIN_PRC, max_gap_prc=MAX_PRC,
                    scale_with_width=True, show=False, save=False):
    gray_img = detect_edges(img)
    bgr_img = cv.cvtColor(gray_img, cv.COLOR_GRAY2BGR)
    theta = to_radians(theta_deg)
    height, width = gray_img.shape[:2]
    if scale_with_width:
        line_scaler = width
    else:
        line_scaler = height

    lines = cv.HoughLinesP(gray_img,
                            rho,
                            theta,
                            threshold,
                            None,
                            min_line_prc * line_scaler / 100,
                            max_gap_prc * line_scaler / 100)

    if lines is not None:
        for i in range(0, len(lines)):
            l = lines[i][0]
            cv.line(bgr_img, (l[0], l[1]), (l[2], l[3]), (0, 0, 255),
                    thickness=1, lineType=cv.LINE_AA)

    title = (f'phough ({rho},{theta_deg},{threshold},{min_line_prc}%,'
            f'{max_gap_prc}%)')
    if show:
        bgr_imshow(title, bgr_img)
    if save:
        path = DIR + "rotate/" + title + ".png"
        cv.imwrite(path, bgr_img)
    return lines


''' Dewarps an image. Assumes input is already denoised. The output color
    scheme matches input (gray or RGB). '''
def dewarp(img, is_rgb=False):
    if is_rgb:
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    best_angle = optimize(img)
    dewarped = rotate(img, best_angle, is_rgb=False)
    if is_rgb:
        dewarped = cv.cvtColor(dewarped, cv.COLOR_GRAY2RGB)
    return dewarped


def find_verticals(img, show=False):
    # Find candidate lines
    height, width = img.shape[:2]
    rho = 1     # 1 pixel
    theta_deg = 0.1 # 0.1 degree
    threshold = int(height * 0.1) #100
    lines, coords = std_houghlines(img, rho=rho, theta_deg=theta_deg,
                                threshold=threshold, show=False, save=False)

    # Collect 2 clusters of vertical lines: one leftmost, one rightmost
    max_slope = 45
    max_theta = to_radians(max_slope) #45)
    min_theta = to_radians(180 - max_slope)

    lefts = None
    rights = None
    all_verticals = []
    
    marg = 10 #px
    page_xc = width / 2
    for line, coord in zip(lines, coords):
        line = tuple(line[0])
        line_theta = get_theta(line)
        seems_vertical = line_theta <= max_theta or line_theta >= min_theta
        if seems_vertical:
            all_verticals.append((line, coord))
            this_xc = get_vertical_xcenter(coord, height)

            if lefts is None:
                lefts = [(line, coord)]
            else:
                on_left_half = this_xc < page_xc
                if on_left_half:
                    left_xc = np.mean([get_vertical_xcenter(coord,height) for
                                line,coord in lefts])

                    is_lefter = this_xc < left_xc
                    is_close = (this_xc <= left_xc + marg and
                                this_xc >= left_xc - marg)

                    if is_lefter and not is_close:
                        lefts = [(line, coord)]
                    elif is_close:
                        lefts.append((line, coord))

            if rights is None:
                rights = [(line, coord)]
            else:
                on_right_half = this_xc > page_xc
                if on_right_half:
                    right_xc = np.mean([get_vertical_xcenter(coord,height) for
                                line,coord in rights])

                    is_righter = this_xc > right_xc
                    is_close = (this_xc <= right_xc + marg and
                                this_xc >= right_xc - marg)

                    if is_righter and not is_close:
                        rights = [(line, coord)]
                    elif is_close:
                        rights.append((line, coord))
    
    lefts_coords = [coord for _,coord in lefts]
    rights_coords = [coord for _,coord in rights]
    avg_left_coords = get_avg_coords(lefts_coords)
    avg_right_coords = get_avg_coords(rights_coords)
    # show_points = lefts_coords + rights_coords
    show_points = [avg_left_coords, avg_right_coords]
    if show:
        bgr_img = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
        for (pt1, pt2) in show_points:
            cv.line(bgr_img, pt1, pt2, (0, 0, 255), thickness=1,
                            lineType=cv.LINE_AA)
            xc, yc = get_vertical_center((pt1, pt2), height)
            cv.circle(bgr_img, (xc,yc), radius=4, color=(0,255,0), thickness=1)
        bgr_imshow("main 2 verticals", bgr_img)
    return lines, coords

def to_radians(degrees):
    return np.pi * degrees / 180

def get_center(line_coords):
    (x1, y1), (x2, y2) = line_coords
    xc = np.mean([x1,x2])
    yc = np.mean([y1,y2])
    return xc, yc

def get_xcenter(line_coords):
    xc, yc = get_center(line_coords)
    return xc

def get_vertical_center(line_coords, page_height):
    (x1, y1), (x2, y2) = line_coords
    yc = page_height // 2
    xc = x1 + (x2-x1)/(y2-y1)*(yc-y1)
    return int(xc), int(yc)

def get_vertical_xcenter(line_coords, page_height):
    xc, yc = get_vertical_center(line_coords, page_height)
    return xc

def get_avg_coords(lines_coords):
    lines_coords_downwards = []
    for p1,p2 in lines_coords:
        x1, y1 = p1
        x2, y2 = p2
        if y1 < y2:
            downwards_coord = (p1,p2)
        else:
            downwards_coord = (p2,p1)
        lines_coords_downwards.append(downwards_coord)
    avg_coords = np.mean(lines_coords_downwards, axis=0)
    avg_coord = avg_coords.astype(int)
    return list(map(tuple, avg_coord))

def get_theta(line):
    return line[1]

if __name__ == "__main__":
    # img = denoise(cv.imread(INPUT_PATH, cv.IMREAD_GRAYSCALE))
    # dewarped = dewarp(img)
    # cv.imwrite(OUTPUT_PATH, dewarped)

    img = denoise(cv.imread("blocks1.png", cv.IMREAD_GRAYSCALE))
    find_verticals(img, show=True)
