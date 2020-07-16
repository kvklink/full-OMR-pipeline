import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv

def imshow(title, image, use_plt=True, is_bgr = False):
    if use_plt:
        plt.figure()
        if is_bgr:
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        plt.imshow(image)
        plt.title(title)
        plt.show()
    else:
        cv.imshow(title, image)
    return


def bgr_imshow(title, image, use_plt=True):
    return imshow(title, image, use_plt, is_bgr=True)


def get_dir(file_path):
    return file_path[::-1].split('/',1)[1][::-1]

def to_radians(degrees):
    return np.pi * degrees / 180