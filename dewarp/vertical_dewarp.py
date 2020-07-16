import numpy as np

from utils.util import *
from dewarp.deskew import std_houghlines

''' Assumes image is already dewarped horizontally '''
def dewarp_vertical(img):
    blocks_img = make_blocks(img)
    keypoints = find_keypoints(blocks_img, show=False)
    dewarped_ver = fix_verticals(img, keypoints)
    return dewarped_ver


def make_blocks(img):
    rows, cols = img.shape[:2]

    img_struct = img.copy()
    gray = cv.cvtColor(img_struct, cv.COLOR_BGR2GRAY)

    (thresh, im_bw) = cv.threshold(gray, 200, 255, cv.THRESH_BINARY)# | cv.THRESH_OTSU)

    erode_struct = cv.getStructuringElement(cv.MORPH_RECT, (1, 50))
    dilate_struct = cv.getStructuringElement(cv.MORPH_RECT, (20, 1))
    
    step1 = cv.dilate(im_bw, dilate_struct, 1)
    # bgr_imshow("dilate", step1)
    step2 = cv.erode(step1, erode_struct, 1)
    # bgr_imshow("erode", step2)
    im_inv = cv.bitwise_not(step2)
    # bgr_imshow("blocks made", im_inv)
    # cv.imwrite("blocks.png", im_inv)
    return im_inv

def find_verticals(img, show=False):
    # Find candidate vertical lines
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
            all_verticals.append(coord)
            this_xc = get_vertical_xcenter(coord, height)

            if lefts is None:
                lefts = [coord]
            else:
                on_left_half = this_xc < page_xc
                if on_left_half:
                    left_xc = np.mean([get_vertical_xcenter(coord,height) for
                                coord in lefts])

                    is_lefter = this_xc < left_xc
                    is_close = (this_xc <= left_xc + marg and
                                this_xc >= left_xc - marg)

                    if is_lefter and not is_close:
                        lefts = [coord]
                    elif is_close:
                        lefts.append(coord)

            if rights is None:
                rights = [coord]
            else:
                on_right_half = this_xc > page_xc
                if on_right_half:
                    right_xc = np.mean([get_vertical_xcenter(coord,height) for
                                coord in rights])

                    is_righter = this_xc > right_xc
                    is_close = (this_xc <= right_xc + marg and
                                this_xc >= right_xc - marg)

                    if is_righter and not is_close:
                        rights = [coord]
                    elif is_close:
                        rights.append(coord)
    
    avg_left = get_avg_coords(lefts)
    avg_right = get_avg_coords(rights)
    # show_points = lefts + rights
    show_points = [avg_left, avg_right]
    if show:
        bgr_img = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
        for (pt1, pt2) in show_points:
            cv.line(bgr_img, pt1, pt2, (0, 0, 255), thickness=2,
                            lineType=cv.LINE_AA)
            xc, yc = get_vertical_center((pt1, pt2), height)
            cv.circle(bgr_img, (xc,yc), radius=4, color=(0,255,0), thickness=2)
        bgr_imshow("main 2 verticals", bgr_img)
    return avg_left, avg_right


def find_keypoints(img, show=False):
    avg_left, avg_right = find_verticals(img, show)
    topl, botl = avg_left
    topr, botr = avg_right
    return (topl, topr, botl, botr)


def fix_verticals(img, keypoints):
    height, width = img.shape[:2]
    
    topl, topr, botl, botr = [list(kp) for kp in keypoints]
    topl_x = topl[0]
    topr_x = topr[0]
    botl_y = botl[1]
    botr_y = botr[1]
    src_m = np.array([topl, botl, topr, botr])
    dst_m = np.array([topl, (topl_x, botl_y), topr, (topr_x, botr_y)])

    h, status = cv.findHomography(src_m, dst_m)
    img_new = cv.warpPerspective(img, h, (width, height))
    # bgr_imshow("Fix verticals", img_new)
    return img_new


####### Helper methods

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
    img = cv.imread("blocks1.png", cv.IMREAD_GRAYSCALE)
    find_verticals(img, show=True)