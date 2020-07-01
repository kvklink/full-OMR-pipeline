import math

import cv2


def calc_avg_distance(lines):
    s = [x[1] for x in lines]
    e = [x[3] for x in lines]
    diff_s = [j - i for i, j in zip(s[:-1], s[1:])]
    diff_e = [j - i for i, j in zip(e[:-1], e[1:])]
    ds = sum(diff_s) / len(diff_s)
    de = sum(diff_e) / len(diff_e)
    return int((ds + de) / 2)


def calc_lower_lines(lines, dist, width):
    # create all(4) the lines below the bar
    s = [x[1] for x in lines]
    e = [x[3] for x in lines]

    s_bottom = max(s)
    e_bottom = max(e)

    new_lines = lines.copy()
    for i in range(1, 5):
        new_line = [0, s_bottom + (i * dist), width, e_bottom + (i * dist)]
        new_lines.append(new_line)

    return new_lines


def calc_higher_lines(lines, dist, width):
    # create all(4) the lines above the bar
    s = [x[1] for x in lines]
    e = [x[3] for x in lines]

    s_top = min(s)
    e_top = min(e)

    new_lines = lines.copy()
    for i in range(1, 5):
        new_line = [0, s_top - (i * dist), width, e_top - (i * dist)]
        new_lines.append(new_line)

    return new_lines


def calc_y(line, x):
    x1 = line[0]
    y1 = line[1]
    x2 = line[2]
    y2 = line[3]

    y = x * (y2 - y1) / (x2 - x1) + ((x2 * y1 - x1 * y2) / (x2 - x1))
    return int(y)


def detect_staff_lines(img_bar):
    height, width = img_bar.shape[:2]
    img_copy = img_bar.copy()

    # Canny edge detection

    img_struct_hor = img_copy.copy()
    hor_size = round(img_struct_hor.shape[1] / 30)
    hor_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (hor_size, 1))

    img_struct_hor3 = cv2.dilate(img_struct_hor, hor_struct, 1)
    eroted = cv2.erode(img_struct_hor3, hor_struct, 3)

    gray = cv2.cvtColor(eroted, cv2.COLOR_BGR2GRAY)
    (thresh, img_bw) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    gray2 = cv2.cvtColor(img_bw, cv2.COLOR_GRAY2BGR)

    edges2 = cv2.Canny(gray2, 100, 200)

    # Find Hough lines

    # getallen nog aanpassen naar schaalbaar tov img size
    lines = cv2.HoughLinesP(edges2, 1, math.pi / 2, 1, None, 50, 10)
    #        lines = cv2.HoughLines(edges2, 1, math.pi/2, 1, None)

    # Label useless lines for removal and combine consecutive lines

    for i, linearr in enumerate(lines):
        line = linearr[0]
        pt1 = (line[0], line[1])
        pt2 = (line[2], line[3])
        xlen1 = pt2[0] - pt1[0]
        ylen1 = pt2[1] - pt1[1]
        rot1 = math.degrees(math.atan(ylen1 / xlen1))
        # print('start = %d,%d, end = %d,%d, xlen = %d, ylen = %d'%(pt1[0],pt1[1],pt2[0],pt2[1],xlen1,ylen1))
        # print(rot1)
        if abs(rot1) >= 3:
            lines[i] = [[0, 0, 0, 0]]

    for i, linearr in enumerate(lines):
        #         print(linearr)
        line = linearr[0]
        pt1 = (line[0], line[1])
        pt2 = (line[2], line[3])
        for j, linearr2 in enumerate(lines):
            line2 = linearr2[0]
            pt3 = (line2[0], line2[1])
            pt4 = (line2[2], line2[3])
            if pt3[0] in range(pt1[0] + 1, pt2[0] + 2) and pt3[1] in range(pt2[1] - 1, pt2[1] + 2):
                if pt4[0] > pt2[0]:
                    xlen1 = pt2[0] - pt1[0]
                    ylen1 = pt2[1] - pt1[1]
                    xlen2 = pt4[0] - pt3[0]
                    ylen2 = pt4[1] - pt3[1]
                    rot1 = math.degrees(math.atan(ylen1 / xlen1))
                    rot2 = math.degrees(math.atan(ylen2 / xlen2))
                    #             print('%f vs. %f'%(rot1,rot2))
                    if abs(rot1 - rot2) < 3:
                        lines[j] = [[pt1[0], pt1[1], pt4[0], pt4[1]]]
                        lines[i] = [[0, 0, 0, 0]]
                        break
                else:
                    lines[j] = [[0, 0, 0, 0]]

    for i, linearr in enumerate(lines):
        line = linearr[0]
        pt1 = (line[0], line[1])
        pt2 = (line[2], line[3])
        xlen1 = pt2[0] - pt1[0]
        if xlen1 < width / 4:
            lines[i] = [[0, 0, 0, 0]]

    # Remove labeled lines

    new_lines = []
    for linearr in lines:
        line = linearr[0]
        if line.all() == 0:
            continue
        new_lines.append(line)

    # Stretch lines across entire image

    long_lines = []

    for n, line in enumerate(new_lines):
        new_p1_x = 0
        new_p1_y = calc_y(line, new_p1_x)

        new_p2_x = width
        new_p2_y = calc_y(line, new_p2_x)

        long_lines.append([new_p1_x, new_p1_y, new_p2_x, new_p2_y])

    # Remove (semi-)duplicate lines

    long_lines = sorted(long_lines, key=lambda x: x[1])
    unique_lines = []

    for i, l in enumerate(long_lines):
        if i == 0:
            continue
        if l[1] - long_lines[i - 1][1] > 3:
            unique_lines.append(long_lines[i - 1])
            if i == len(long_lines) - 1:
                unique_lines.append(l)
        elif i == len(long_lines) - 1:
            unique_lines.append(long_lines[i - 1])

    for i in range(len(unique_lines)):
        unique_lines[i][1] = unique_lines[i][1] + 1
        unique_lines[i][3] = unique_lines[i][3] + 1

    return unique_lines


def find_rect(self, group):
    min_x, min_y = (group[0].x, group[0].y)
    max_x, max_y = (min_x, min_y)
    for acc in group:
        min_x = min(min_x, acc.x)
        max_x = max(max_x, acc.x + acc.w)
        min_y = min(min_y, acc.y)
        max_y = max(max_y, acc.y + acc.h)
    w = max_x - min_x
    h = max_y - min_y
    return min_x, min_y, w, h
