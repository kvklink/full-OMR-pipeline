import cv2 as cv
import imutils as imutils
import numpy as np
from tqdm import tqdm


def template_matching(img_rgb):
    template_dir = '/Users/kyle/Documents/UT/ACVPR/Rebelo Dataset/database/syn/notes/'
    img_gray = cv.cvtColor(img_rgb, cv.COLOR_BGR2GRAY)

    # for file in listdir(template_dir):
    #     templates.append(cv.imread(template_dir + file, 0))

    templates = []
    selected = [10186, 10650, 10146, 10825, 11414, 11565, 1020]
    for select in selected:
        templates.append(cv.Canny(cv.cvtColor(cv.imread(template_dir + f'symbol{select}.png'), cv.COLOR_BGR2GRAY)), 50,
                         200)

    threshold = 0.75
    for template in tqdm(templates):
        w, h = template.shape[::-1]

        # loop over the scales of the image
        for scale in np.linspace(0.2, 1.0, 20)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(img_gray, width=int(img_gray.shape[1] * scale))
            r = img_gray.shape[1] / float(resized.shape[1])
            # if the resized image is smaller than the template, then break
            # from the loop
            if resized.shape[0] < h or resized.shape[1] < w:
                break

        res = cv.matchTemplate(img_gray, template, cv.TM_CCOEFF_NORMED)

        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            cv.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)

    return img_rgb


if __name__ == "__main__":
    cv.namedWindow('output', cv.WINDOW_NORMAL)
    cv.resizeWindow('output', 1100, 1100)
    cv.imshow('output', template_matching('/Users/kyle/Desktop/input.jpeg'))
    cv.waitKey(0)
    cv.destroyAllWindows()
̵
