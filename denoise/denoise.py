import cv2 as cv


def denoise(input_name):
    img_color = cv.imread(input_name)
    img_gray = cv.cvtColor(img_color, cv.COLOR_BGR2GRAY)
    cv.normalize(img_gray, img_gray, 0, 165, cv.NORM_MINMAX)

    # is dit netjes?
    img_gray = cv.bitwise_not(img_gray)
    # nee
    _, img_gray = cv.threshold(img_gray, 255, 0, cv.THRESH_TRUNC)
    _, img = cv.threshold(img_gray, 127, 0, cv.THRESH_TOZERO)
    # werkt het?
    img = cv.bitwise_not(img)
    # ja
    return cv.fastNlMeansDenoising(img, None, 20, 7, 21)


if __name__ == "__main__":
    cv.imshow('output', denoise('/Users/kyle/Desktop/test.png'))
    cv.waitKey(0)
    cv.destroyAllWindows()
    cv.waitKey(1)
