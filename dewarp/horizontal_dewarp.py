#!/usr/bin/env python
######################################################################
# page_dewarp.py - Proof-of-concept of page-dewarping based on a
# "cubic sheet" model. Requires OpenCV (version 3 or greater),
# PIL/Pillow, and scipy.optimize.
######################################################################
# Author:  Matt Zucker
# Date:    July 2016
# License: MIT License
######################################################################
# Edits by Lindsay Kempen (Summer 2020):
# - Updated for python 3.7 and newer versions of OpenCV
# - Tweaked params and functions for OMR purposes
# - Added spacious margins to allow space for severe warping
# - Removed main()
######################################################################

import os
import sys
import datetime
import cv2 as cv
from PIL import Image
import numpy as np
import scipy.optimize

from utils.util import imshow, bgr_imshow

# for some reason pylint complains about cv members being undefined :(
# pylint: disable=E1101

HEIGHT_MARGIN_PERC = 10
WIDTH_MARGIN_PERC = 25

PAGE_MARGIN_X = 50       # reduced px to ignore near L/R edge
PAGE_MARGIN_Y = 20       # reduced px to ignore near T/B edge

OUTPUT_ZOOM = 1.0        # how much to zoom output relative to *original* image
REMAP_DECIMATE = 16      # downscaling factor for remapping image

ADAPTIVE_WINSZ = 55      # window size for adaptive threshold in reduced px

TEXT_MIN_WIDTH = 15      # min reduced px width of detected text contour
TEXT_MIN_HEIGHT = 2      # min reduced px height of detected text contour
TEXT_MIN_ASPECT = 1.5    # filter out text contours below this w/h ratio
TEXT_MAX_THICKNESS = 10  # max reduced px thickness of detected text contour

EDGE_MAX_OVERLAP = 1.0   # max reduced px horiz. overlap of contours in span
EDGE_MAX_LENGTH = 100.0  # max reduced px length of edge connecting contours
EDGE_ANGLE_COST = 10.0   # cost of angles in edges (tradeoff vs. length)
EDGE_MAX_ANGLE = 7.5     # maximum change in angle allowed between contours

RVEC_IDX = slice(0, 3)   # index of rvec in params vector
TVEC_IDX = slice(3, 6)   # index of tvec in params vector
CUBIC_IDX = slice(6, 8)  # index of cubic slopes in params vector

# SPAN_MIN_WIDTH_PERC = 60#1000#100#30   
# SPAN_STEP_PERC = 3#50#20#20   
SPAN_MIN_WIDTH_PERC_PORTRAIT = 60  # minimum reduced % img width for span
SPAN_STEP_PERC_PORTRAIT = 10       # % img width spacing for sampling in spans
SPAN_MIN_WIDTH_PERC_LANDSCAPE = 3
SPAN_STEP_PERC_LANDSCAPE = 1.5

FOCAL_LENGTH = 1.2       # normalized focal length of camera

DEBUG_LEVEL = 3          # 0=none, 1=some, 2=lots, 3=all
DEBUG_OUTPUT = 'screen'  # file, screen, both

WINDOW_NAME = 'Dewarp'   # Window name for visualization

# nice color palette for visualizing contours, etc.
CCOLORS = [
    (255, 0, 0),
    (255, 63, 0),
    (255, 127, 0),
    (255, 191, 0),
    (255, 255, 0),
    (191, 255, 0),
    (127, 255, 0),
    (63, 255, 0),
    (0, 255, 0),
    (0, 255, 63),
    (0, 255, 127),
    (0, 255, 191),
    (0, 255, 255),
    (0, 191, 255),
    (0, 127, 255),
    (0, 63, 255),
    (0, 0, 255),
    (63, 0, 255),
    (127, 0, 255),
    (191, 0, 255),
    (255, 0, 255),
    (255, 0, 191),
    (255, 0, 127),
    (255, 0, 63),
]

# default intrinsic parameter matrix
K = np.array([
    [FOCAL_LENGTH, 0, 0],
    [0, FOCAL_LENGTH, 0],
    [0, 0, 1]], dtype=np.float32)


def debug_show(name, step, text, display):

    if DEBUG_OUTPUT != 'screen':
        filetext = text.replace(' ', '_')
        outfile = name + '_debug_' + str(step) + '_' + filetext + '.png'
        cv.imwrite(outfile, display)

    if DEBUG_OUTPUT != 'file':
        image = display.copy()
        height = image.shape[0]

        cv.putText(image, text, (16, height-16),
                    cv.FONT_HERSHEY_SIMPLEX, 1.0,
                    (0, 0, 0), 3, cv.LINE_AA)

        cv.putText(image, text, (16, height-16),
                    cv.FONT_HERSHEY_SIMPLEX, 1.0,
                    (255, 255, 255), 1, cv.LINE_AA)

        bgr_imshow('debug ' + str(step) + ' ' + text, image)


def round_nearest_multiple(i, factor):
    i = int(i)
    rem = i % factor
    if not rem:
        return i
    else:
        return i + factor - rem


def pix2norm(shape, pts):
    height, width = shape[:2]
    scl = 2.0/(max(height, width))
    offset = np.array([width, height], dtype=pts.dtype).reshape((-1, 1, 2))*0.5
    return (pts - offset) * scl


def norm2pix(shape, pts, as_integer):
    height, width = shape[:2]
    scl = max(height, width)*0.5
    offset = np.array([0.5*width, 0.5*height],
                      dtype=pts.dtype).reshape((-1, 1, 2))
    rval = pts * scl + offset
    if as_integer:
        return (rval + 0.5).astype(int)
    else:
        return rval


def fltp(point):
    return tuple(point.astype(int).flatten())


def draw_correspondences(img, dstpoints, projpts):

    display = img.copy()
    dstpoints = norm2pix(img.shape, dstpoints, True)
    projpts = norm2pix(img.shape, projpts, True)

    for pts, color in [(projpts, (255, 0, 0)),
                       (dstpoints, (0, 0, 255))]:

        for point in pts:
            cv.circle(display, fltp(point), 3, color, -1, cv.LINE_AA)

    for point_a, point_b in zip(projpts, dstpoints):
        cv.line(display, fltp(point_a), fltp(point_b),
                 (255, 255, 255), 1, cv.LINE_AA)

    return display


def get_default_params(corners, ycoords, xcoords):

    # page width and height
    page_width = np.linalg.norm(corners[1] - corners[0])
    page_height = np.linalg.norm(corners[-1] - corners[0])
    rough_dims = (page_width, page_height)

    # our initial guess for the cubic has no slope
    cubic_slopes = [0.0, 0.0]

    # object points of flat page in 3D coordinates
    corners_object3d = np.array([
        [0, 0, 0],
        [page_width, 0, 0],
        [page_width, page_height, 0],
        [0, page_height, 0]])

    # estimate rotation and translation from four 2D-to-3D point
    # correspondences
    _, rvec, tvec = cv.solvePnP(corners_object3d,
                                 corners, K, np.zeros(5))

    span_counts = [len(xc) for xc in xcoords]

    params = np.hstack((np.array(rvec).flatten(),
                        np.array(tvec).flatten(),
                        np.array(cubic_slopes).flatten(),
                        ycoords.flatten()) +
                       tuple(xcoords))

    return rough_dims, span_counts, params


def project_xy(xy_coords, pvec):

    # get cubic polynomial coefficients given
    #
    #  f(0) = 0, f'(0) = alpha
    #  f(1) = 0, f'(1) = beta

    alpha, beta = tuple(pvec[CUBIC_IDX])

    poly = np.array([
        alpha + beta,
        -2*alpha - beta,
        alpha,
        0])

    xy_coords = xy_coords.reshape((-1, 2))
    z_coords = np.polyval(poly, xy_coords[:, 0])

    objpoints = np.hstack((xy_coords, z_coords.reshape((-1, 1))))

    image_points, _ = cv.projectPoints(objpoints,
                                        pvec[RVEC_IDX],
                                        pvec[TVEC_IDX],
                                        K, np.zeros(5))

    return image_points


def project_keypoints(pvec, keypoint_index):

    xy_coords = pvec[keypoint_index]
    xy_coords[0, :] = 0

    return project_xy(xy_coords, pvec)


def resize_to_screen(src, maxw=1280, maxh=700, copy=False):

    height, width = src.shape[:2]

    scl_x = float(width)/maxw
    scl_y = float(height)/maxh

    scl = int(np.ceil(max(scl_x, scl_y)))

    if scl > 1.0:
        inv_scl = 1.0/scl
        img = cv.resize(src, (0, 0), None, inv_scl, inv_scl, cv.INTER_AREA)
    elif copy:
        img = src.copy()
    else:
        img = src

    return img


def box(width, height):
    return np.ones((height, width), dtype=np.uint8)


def get_page_extents(small, margins):

    shape = small.shape[:2]
    height, width = shape
    y_marg, x_marg = margins

    page_margin_x = max(PAGE_MARGIN_X, x_marg)
    page_margin_y = max(PAGE_MARGIN_Y, y_marg)
        
    xmin = page_margin_x
    ymin = page_margin_y
    xmax = width-page_margin_x
    ymax = height-page_margin_y

    page = np.zeros((height, width), dtype=np.uint8)
    cv.rectangle(page, (xmin, ymin), (xmax, ymax), (255, 255, 255), -1)

    outline = np.array([
        [xmin, ymin],
        [xmin, ymax],
        [xmax, ymax],
        [xmax, ymin]])

    return page, outline


def get_mask(name, small, pagemask, masktype, erode_iterations):

    sgray = cv.cvtColor(small, cv.COLOR_RGB2GRAY)

    if masktype == 'text':

        mask = cv.adaptiveThreshold(sgray, 255, cv.ADAPTIVE_THRESH_MEAN_C,
                                     cv.THRESH_BINARY_INV,
                                     ADAPTIVE_WINSZ,
                                     25)

        if DEBUG_LEVEL >= 3:
            debug_show(name, 0.1, 'thresholded', mask)

        mask = cv.dilate(mask, box(9, 1))

        if DEBUG_LEVEL >= 3:
            debug_show(name, 0.2, 'dilated', mask)

        mask = cv.erode(mask, box(1, 3))

        if DEBUG_LEVEL >= 3:
            debug_show(name, 0.3, 'eroded', mask)

    else:

        mask = cv.adaptiveThreshold(sgray, 255, cv.ADAPTIVE_THRESH_MEAN_C,
                                     cv.THRESH_BINARY_INV,
                                     ADAPTIVE_WINSZ,
                                     7)

        if DEBUG_LEVEL >= 3:
            debug_show(name, 0.4, 'thresholded', mask)

        mask = cv.erode(mask, box(5, 1), iterations=erode_iterations)

        if DEBUG_LEVEL >= 3:
            debug_show(name, 0.5, 'eroded', mask)

        mask = cv.dilate(mask, box(8, 2))

        if DEBUG_LEVEL >= 3:
            debug_show(name, 0.6, 'dilated', mask)

    return np.minimum(mask, pagemask)


def interval_measure_overlap(int_a, int_b):
    return min(int_a[1], int_b[1]) - max(int_a[0], int_b[0])


def angle_dist(angle_b, angle_a):

    diff = angle_b - angle_a

    while diff > np.pi:
        diff -= 2*np.pi

    while diff < -np.pi:
        diff += 2*np.pi

    return np.abs(diff)


def blob_mean_and_tangent(contour):

    moments = cv.moments(contour)

    area = moments['m00']

    # Add 1e-5 to avoid division by zero
    mean_x = moments['m10'] / (area + 1e-5)
    mean_y = moments['m01'] / (area + 1e-5)

    moments_matrix = np.array([
        [moments['mu20'], moments['mu11']],
        [moments['mu11'], moments['mu02']]
    ]) / (area + 1e-5)

    _, svd_u, _ = cv.SVDecomp(moments_matrix)

    center = np.array([mean_x, mean_y])
    tangent = svd_u[:, 0].flatten().copy()

    return center, tangent


class ContourInfo(object):

    def __init__(self, contour, rect, mask):

        self.contour = contour
        self.rect = rect
        self.mask = mask

        self.center, self.tangent = blob_mean_and_tangent(contour)

        self.angle = np.arctan2(self.tangent[1], self.tangent[0])

        clx = [self.proj_x(point) for point in contour]

        lxmin = min(clx)
        lxmax = max(clx)

        self.local_xrng = (lxmin, lxmax)

        self.point0 = self.center + self.tangent * lxmin
        self.point1 = self.center + self.tangent * lxmax

        self.pred = None
        self.succ = None

    def proj_x(self, point):
        return np.dot(self.tangent, point.flatten()-self.center)

    def local_overlap(self, other):
        xmin = self.proj_x(other.point0)
        xmax = self.proj_x(other.point1)
        return interval_measure_overlap(self.local_xrng, (xmin, xmax))


def generate_candidate_edge(cinfo_a, cinfo_b):

    # we want a left of b (so a's successor will be b and b's
    # predecessor will be a) make sure right endpoint of b is to the
    # right of left endpoint of a.
    if cinfo_a.point0[0] > cinfo_b.point1[0]:
        tmp = cinfo_a
        cinfo_a = cinfo_b
        cinfo_b = tmp

    x_overlap_a = cinfo_a.local_overlap(cinfo_b)
    x_overlap_b = cinfo_b.local_overlap(cinfo_a)

    overall_tangent = cinfo_b.center - cinfo_a.center
    overall_angle = np.arctan2(overall_tangent[1], overall_tangent[0])

    delta_angle = max(angle_dist(cinfo_a.angle, overall_angle),
                      angle_dist(cinfo_b.angle, overall_angle)) * 180/np.pi

    # we want the largest overlap in x to be small
    x_overlap = max(x_overlap_a, x_overlap_b)

    dist = np.linalg.norm(cinfo_b.point0 - cinfo_a.point1)

    if (dist > EDGE_MAX_LENGTH or
            x_overlap > EDGE_MAX_OVERLAP or
            delta_angle > EDGE_MAX_ANGLE):
        return None
    else:
        score = dist + delta_angle*EDGE_ANGLE_COST
        return (score, cinfo_a, cinfo_b)


def make_tight_mask(contour, xmin, ymin, width, height):

    tight_mask = np.zeros((height, width), dtype=np.uint8)
    tight_contour = contour - np.array((xmin, ymin)).reshape((-1, 1, 2))

    cv.drawContours(tight_mask, [tight_contour], 0,
                     (1, 1, 1), -1)

    return tight_mask


def get_contours(name, small, pagemask, masktype, erode_iterations):

    mask = get_mask(name, small, pagemask, masktype, erode_iterations)

    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL,
                                      cv.CHAIN_APPROX_NONE)

    contours_out = []

    for contour in contours:

        rect = cv.boundingRect(contour)
        xmin, ymin, width, height = rect

        if (width < TEXT_MIN_WIDTH or
                height < TEXT_MIN_HEIGHT or
                width < TEXT_MIN_ASPECT*height):
            continue

        tight_mask = make_tight_mask(contour, xmin, ymin, width, height)

        if tight_mask.sum(axis=0).max() > TEXT_MAX_THICKNESS:
            continue

        contours_out.append(ContourInfo(contour, rect, tight_mask))

    if DEBUG_LEVEL >= 2:
        visualize_contours(name, small, contours_out)

    return contours_out


def assemble_spans(name, small, pagemask, cinfo_list, margins):

    # sort list
    cinfo_list = sorted(cinfo_list, key=lambda cinfo: cinfo.rect[1])

    # generate all candidate edges
    candidate_edges = []

    for i, cinfo_i in enumerate(cinfo_list):
        for j in range(i):
            # note e is of the form (score, left_cinfo, right_cinfo)
            edge = generate_candidate_edge(cinfo_i, cinfo_list[j])
            if edge is not None:
                candidate_edges.append(edge)

    # sort candidate edges by score (lower is better)
    candidate_edges.sort()

    # for each candidate edge
    for _, cinfo_a, cinfo_b in candidate_edges:
        # if left and right are unassigned, join them
        if cinfo_a.succ is None and cinfo_b.pred is None:
            cinfo_a.succ = cinfo_b
            cinfo_b.pred = cinfo_a

    # generate list of spans as output
    spans = []

    # until we have removed everything from the list
    while cinfo_list:

        # get the first on the list
        cinfo = cinfo_list[0]

        # keep following predecessors until none exists
        while cinfo.pred:
            cinfo = cinfo.pred

        # start a new span
        cur_span = []

        width = 0.0

        # follow successors til end of span
        while cinfo:
            # remove from list (sadly making this loop *also* O(n^2)
            cinfo_list.remove(cinfo)
            # add to span
            cur_span.append(cinfo)
            width += cinfo.local_xrng[1] - cinfo.local_xrng[0]
            # set successor
            cinfo = cinfo.succ

        # add if long enough
        shape = small.shape[:2]
        img_height, img_width = get_orig_shape(shape, margins)
        if img_height > img_width:
            span_min_width = SPAN_MIN_WIDTH_PERC_PORTRAIT
        else:
            span_min_width = SPAN_MIN_WIDTH_PERC_LANDSCAPE
        if width > span_min_width / 100 * img_width:
            spans.append(cur_span)

    if DEBUG_LEVEL >= 2:
        visualize_spans(name, small, pagemask, spans)

    return spans


def sample_spans(shape, spans, margins):

    span_points = []

    for span in spans:

        contour_points = []

        for cinfo in span:

            yvals = np.arange(cinfo.mask.shape[0]).reshape((-1, 1))
            totals = (yvals * cinfo.mask).sum(axis=0)
            means = totals / cinfo.mask.sum(axis=0)

            xmin, ymin = cinfo.rect[:2]
            # widt, heig = cinfo.rect[2:]

            img_height, img_width = get_orig_shape(shape, margins)
            
            if img_height > img_width:
                span_step_perc = SPAN_STEP_PERC_PORTRAIT
            else:
                span_step_perc = SPAN_STEP_PERC_LANDSCAPE
            step = int(span_step_perc / 100 * img_width)
            start = ((len(means)-1) % step) // 2

            contour_points += [(x+xmin, means[x]+ymin)
                               for x in range(start, len(means), step)]

            # contour_points.append((xmin, ymin))
            # contour_points.append((xmin + widt, ymin + heig))
        contour_points = np.array(contour_points,
                                  dtype=np.float32).reshape((-1, 1, 2))

        contour_points = pix2norm(shape, contour_points)

        span_points.append(contour_points)

    return span_points


def keypoints_from_samples(name, small, pagemask, page_outline,
                           span_points):

    all_evecs = np.array([[0.0, 0.0]])
    all_weights = 0

    for points in span_points:

        _, evec = cv.PCACompute(points.reshape((-1, 2)),
                                 None, maxComponents=1)

        weight = np.linalg.norm(points[-1] - points[0])

        all_evecs += evec * weight
        all_weights += weight

    evec = all_evecs / all_weights

    x_dir = evec.flatten()

    if x_dir[0] < 0:
        x_dir = -x_dir

    y_dir = np.array([-x_dir[1], x_dir[0]])

    pagecoords = cv.convexHull(page_outline)
    pagecoords = pix2norm(pagemask.shape, pagecoords.reshape((-1, 1, 2)))
    pagecoords = pagecoords.reshape((-1, 2))

    px_coords = np.dot(pagecoords, x_dir)
    py_coords = np.dot(pagecoords, y_dir)

    px0 = px_coords.min()
    px1 = px_coords.max()

    py0 = py_coords.min()
    py1 = py_coords.max()

    p00 = px0 * x_dir + py0 * y_dir
    p10 = px1 * x_dir + py0 * y_dir
    p11 = px1 * x_dir + py1 * y_dir
    p01 = px0 * x_dir + py1 * y_dir

    corners = np.vstack((p00, p10, p11, p01)).reshape((-1, 1, 2))

    ycoords = []
    xcoords = []

    for points in span_points:
        pts = points.reshape((-1, 2))
        px_coords = np.dot(pts, x_dir)
        py_coords = np.dot(pts, y_dir)
        ycoords.append(py_coords.mean() - py0)
        xcoords.append(px_coords - px0)

    if DEBUG_LEVEL >= 2:
        visualize_span_points(name, small, span_points, corners)

    return corners, np.array(ycoords), xcoords


def visualize_contours(name, small, cinfo_list):

    regions = np.zeros_like(small)

    for j, cinfo in enumerate(cinfo_list):

        cv.drawContours(regions, [cinfo.contour], 0,
                         CCOLORS[j % len(CCOLORS)], -1)

    mask = (regions.max(axis=2) != 0)

    display = small.copy()
    display[mask] = (display[mask]/2) + (regions[mask]/2)

    for j, cinfo in enumerate(cinfo_list):
        color = CCOLORS[j % len(CCOLORS)]
        color = tuple([c/4 for c in color])

        cv.circle(display, fltp(cinfo.center), 3,
                   (255, 255, 255), 1, cv.LINE_AA)

        cv.line(display, fltp(cinfo.point0), fltp(cinfo.point1),
                 (255, 255, 255), 1, cv.LINE_AA)

    debug_show(name, 1, 'contours', display)


def visualize_spans(name, small, pagemask, spans):

    regions = np.zeros_like(small)

    for i, span in enumerate(spans):
        contours = [cinfo.contour for cinfo in span]
        cv.drawContours(regions, contours, -1,
                         CCOLORS[i*3 % len(CCOLORS)], -1)

    mask = (regions.max(axis=2) != 0)

    display = small.copy()
    display[mask] = (display[mask]/2) + (regions[mask]/2)
    display[pagemask == 0] //= 4

    debug_show(name, 2, 'spans', display)


def visualize_span_points(name, small, span_points, corners):

    display = small.copy()

    for i, points in enumerate(span_points):

        points = norm2pix(small.shape, points, False)

        mean, small_evec = cv.PCACompute(points.reshape((-1, 2)),
                                          None,
                                          maxComponents=1)

        dps = np.dot(points.reshape((-1, 2)), small_evec.reshape((2, 1)))
        dpm = np.dot(mean.flatten(), small_evec.flatten())

        point0 = mean + small_evec * (dps.min()-dpm)
        point1 = mean + small_evec * (dps.max()-dpm)

        for point in points:
            cv.circle(display, fltp(point), 3,
                       CCOLORS[i % len(CCOLORS)], -1, cv.LINE_AA)

        cv.line(display, fltp(point0), fltp(point1),
                 (255, 255, 255), 1, cv.LINE_AA)

    cv.polylines(display, [norm2pix(small.shape, corners, True)],
                  True, (255, 255, 255))

    debug_show(name, 3, 'span points', display)


def imgsize(img):
    height, width = img.shape[:2]
    return '{}x{}'.format(width, height)


def make_keypoint_index(span_counts):

    nspans = len(span_counts)
    npts = sum(span_counts)
    keypoint_index = np.zeros((npts+1, 2), dtype=int)
    start = 1

    for i, count in enumerate(span_counts):
        end = start + count
        keypoint_index[start:start+end, 1] = 8+i
        start = end

    keypoint_index[1:, 0] = np.arange(npts) + 8 + nspans

    return keypoint_index


def optimize_params(name, small, dstpoints, span_counts, params):

    keypoint_index = make_keypoint_index(span_counts)

    def objective(pvec):
        ppts = project_keypoints(pvec, keypoint_index)
        return np.sum((dstpoints - ppts)**2)

    print('  initial objective is', objective(params))

    if DEBUG_LEVEL >= 1:
        projpts = project_keypoints(params, keypoint_index)
        display = draw_correspondences(small, dstpoints, projpts)
        debug_show(name, 4, 'keypoints before', display)

    print('  optimizing', len(params), 'parameters...')
    start = datetime.datetime.now()
    res = scipy.optimize.minimize(objective, params,
                                  method='Powell')
    end = datetime.datetime.now()
    print('  optimization took', round((end-start).total_seconds(), 2), 'sec.')
    print('  final objective is', res.fun)
    params = res.x

    if DEBUG_LEVEL >= 1:
        projpts = project_keypoints(params, keypoint_index)
        display = draw_correspondences(small, dstpoints, projpts)
        debug_show(name, 5, 'keypoints after', display)

    return params


def get_page_dims(corners, rough_dims, params):

    dst_br = corners[2].flatten()

    dims = np.array(rough_dims)

    def objective(dims):
        proj_br = project_xy(dims, params)
        return np.sum((dst_br - proj_br.flatten())**2)

    res = scipy.optimize.minimize(objective, dims, method='Powell')
    dims = res.x

    print('  got page dims', dims[0], 'x', dims[1])

    return dims


def remap_image(name, img, small, page_dims, params):
    # height, width, _ = img.shape
    height = 0.5 * page_dims[1] * OUTPUT_ZOOM * img.shape[0]
    height = round_nearest_multiple(height, REMAP_DECIMATE)

    width = round_nearest_multiple(height * page_dims[0] / page_dims[1],
                                   REMAP_DECIMATE)

    print('  output will be {}x{}'.format(width, height))

    height_small = height // REMAP_DECIMATE
    width_small = width // REMAP_DECIMATE

    page_x_range = np.linspace(0, page_dims[0], width_small)
    page_y_range = np.linspace(0, page_dims[1], height_small)

    page_x_coords, page_y_coords = np.meshgrid(page_x_range, page_y_range)

    page_xy_coords = np.hstack((page_x_coords.flatten().reshape((-1, 1)),
                                page_y_coords.flatten().reshape((-1, 1))))

    page_xy_coords = page_xy_coords.astype(np.float32)

    image_points = project_xy(page_xy_coords, params)
    image_points = norm2pix(img.shape, image_points, False)

    image_x_coords = image_points[:, 0, 0].reshape(page_x_coords.shape)
    image_y_coords = image_points[:, 0, 1].reshape(page_y_coords.shape)

    image_x_coords = cv.resize(image_x_coords, (width, height),
                                interpolation=cv.INTER_CUBIC)

    image_y_coords = cv.resize(image_y_coords, (width, height),
                                interpolation=cv.INTER_CUBIC)

    img_gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)

    remapped = cv.remap(img_gray, image_x_coords, image_y_coords,
                         cv.INTER_CUBIC,
                         dst=None, borderMode=cv.BORDER_CONSTANT)

    if DEBUG_LEVEL >= 2:
        debug_show(name, 6.1, "prethresh", remapped)

    thresh = cv.adaptiveThreshold(remapped, 255, cv.ADAPTIVE_THRESH_MEAN_C,
                                   cv.THRESH_BINARY, ADAPTIVE_WINSZ, 25)

    pil_image = Image.fromarray(thresh)
    pil_image = pil_image.convert('1')

    threshfile = name + '_thresh.png'
    # pil_image.save(threshfile, dpi=(OUTPUT_DPI, OUTPUT_DPI))

    if DEBUG_LEVEL >= 1:
        height = small.shape[0]
        width = int(round(height * float(thresh.shape[1])/thresh.shape[0]))
        display = cv.resize(thresh, (width, height),
                             interpolation=cv.INTER_AREA)
        debug_show(name, 6, 'output', display)

    # LK: Tweaked this to output the remapped image, without any adaptive
    # thresholding
    return threshfile, remapped


# By LK
def dewarp_horizontal_at(imgfile):
    img = cv.imread(imgfile)
    return dewarp_horizontal(img)


# Tweaks by LK
'''Assumes RGB input image'''
def dewarp_horizontal(img, extra_margins=False):
    basename = "input_file" #os.path.basename(imgfile)
    name = "input" #name, _ = os.path.splitext(basename)

    if extra_margins:
        img, margins = make_margins(img)
        # imshow("margins", img)
    else:
        margins = (0, 0)
    small = resize_to_screen(img, maxw=4000, maxh=4000)

    print('loaded', basename, 'with size', imgsize(img),)
    print('and resized to', imgsize(small))

    if DEBUG_LEVEL >= 3:
        debug_show(name, 0.0, 'original', small)

    # Erode more until enough staff lines found
    nspans = -1
    erode_iterations = 3
    while nspans < 10 and erode_iterations < 8:
        pagemask, page_outline = get_page_extents(small, margins)

        cinfo_list = get_contours(name, small, pagemask, 'line', erode_iterations)
        spans = assemble_spans(name, small, pagemask, cinfo_list, margins)
        nspans = len(spans)
        erode_iterations += 1

    if nspans < 1:
        raise RuntimeError(f'Found too few lines ({nspans}) as guideline'
                           'for dewarping')

    span_points = sample_spans(small.shape, spans, margins)

    print('  got', len(spans), 'spans',)
    print('with', sum([len(pts) for pts in span_points]), 'points.')

    corners, ycoords, xcoords = keypoints_from_samples(name, small,
                                                        pagemask,
                                                        page_outline,
                                                        span_points)

    rough_dims, span_counts, params = get_default_params(corners,
                                                            ycoords, xcoords)

    dstpoints = np.vstack((corners[0].reshape((1, 1, 2)),) +
                            tuple(span_points))

    params = optimize_params(name, small,
                                dstpoints,
                                span_counts, params)

    page_dims = get_page_dims(corners, rough_dims, params)

    outfile, remapped = remap_image(name, img, small, page_dims, params)
    remapped = cv.cvtColor(remapped, cv.COLOR_BGR2RGB)
    return remapped


# By LK
def make_margins(img):
    def get_margins(shape):
        img_height, img_width = shape[:2]

        is_portrait = img_height > img_width
        if is_portrait:
            ver_factor = HEIGHT_MARGIN_PERC
            hor_factor = WIDTH_MARGIN_PERC
        else:
            ver_factor = WIDTH_MARGIN_PERC
            hor_factor = HEIGHT_MARGIN_PERC

        ver = int(ver_factor / 100 * img_height)
        hor = int(hor_factor / 100 * img_width)
        return ver, hor

    margins = get_margins(img.shape[:2])
    ver, hor = margins
    white = (255,255,255)
    margined = cv.copyMakeBorder(img, top=ver, bottom=ver, left=hor, right=hor,
                                    borderType=cv.BORDER_CONSTANT, value=white)
    return margined, margins


# By LK
def get_orig_shape(shape, margins):
    return shape[0] - margins[0]*2, shape[1] - margins[1]*2