import cv2 as cv


def denoise(img):
    cv.normalize(img, img, 0, 165, cv.NORM_MINMAX)
    img = cv.bitwise_not(img)
    _, img = cv.threshold(img, 255, 0, cv.THRESH_TRUNC)
    _, img = cv.threshold(img, 127, 0, cv.THRESH_TOZERO)
    img = cv.bitwise_not(img)
    return cv.fastNlMeansDenoising(img, None, 20, 7, 21)

def denoise_at(path):
    return denoise(cv.imread(path, cv.IMREAD_GRAYSCALE))

if __name__ == "__main__":
    cv.imshow('output', denoise_at('/Users/kyle/Desktop/test.png'))
    cv.waitKey(0)
    cv.destroyAllWindows()
    cv.waitKey(1)
