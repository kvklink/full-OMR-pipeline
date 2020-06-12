import cv2 as cv
import numpy as np


def separate_bars(input_file, show=False):
    rows, cols = input_file.shape[:2]
    img_struct = input_file.copy()

    gray = cv.cvtColor(img_struct, cv.COLOR_BGR2GRAY)
    thresh, im_bw = cv.threshold(gray, 128, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)

    erode_struct = cv.getStructuringElement(cv.MORPH_RECT, (1, 20))
    dilate_struct = cv.getStructuringElement(cv.MORPH_RECT, (20, 1))

    step1 = cv.erode(im_bw, erode_struct, 1)
    step2 = cv.dilate(step1, dilate_struct, 1)
    im_inv = cv.bitwise_not(step2)

    img_row_sum = np.sum(im_inv, axis=1).toList()

    threshold = 0.5

    for i, r in enumerate(img_row_sum):
        perc = r / (255 * im_inv.shape[1])
        img_row_sum[i] = perc

    start = []
    end = []
    full = []

    for i, val in enumerate(img_row_sum):
        if i == 0: continue
        if val == threshold:
            pass
        elif val > threshold > img_row_sum[i - 1]:
            start.append(i)
            full.append(i)
        elif val < threshold < img_row_sum[i - 1]:
            end.append(i)
            full.append(i)

    cut = []

    for i, val in enumerate(full):
        if i == 0:
            if val in start and full[i + 2] in start:
                dist = full[i + 2] - val
                cut_location_s = val - dist
                cut.append([max(cut_location_s, 0), full[i + 2]])
        elif i == len(full) - 2 and val in start and full[i - 1] in end and full[i + 1] in end:
            dist = full[i + 1] - full[i - 1]
            cut_location_e = full[i + 1] + dist
            cut.append([full[i - 1], min(cut_location_e, len(img_row_sum) - 1)])
        elif i == len(full) - 1:
            break
        elif val in start and full[i - 1] in end and full[i + 2] in start:
            cut.append([full[i - 1], full[i + 2]])

    staffs = []
    for i in range(len(cut)):
        crop1 = input_file[cut[i][0]:cut[i][1], 0:input_file.shape[1]]
        staffs.append(crop1)

    if show:
        for s in staffs:
            cv.imshow('staffline.detect() -- cropped image', s)
            cv.waitKey(0)
            cv.destroyAllWindows()
            cv.waitKey(1)

    return staffs


def find_barlines(staff_images):
    return None


def measure(input):
    return []
