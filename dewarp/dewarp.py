from dewarp.horizontal_dewarp import dewarp_horizontal
from dewarp.vertical_dewarp import dewarp_vertical
from utils.util import imshow
import cv2 as cv

def dewarp(img, is_rgb=False):
    if not is_rgb:
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)

    dewarped_hor = dewarp_horizontal(img, extra_margins=True)
    # imshow("dewarp horizontally", dewarped_hor)
    dewarped = dewarp_vertical(dewarped_hor)
    # imshow("dewarped whole", dewarped)

    if not is_rgb:
        dewarped = cv.cvtColor(dewarped, cv.COLOR_RGB2GRAY)
    return dewarped