import cv2 as cv

'''Denoises an image. The output color scheme matches input (gray or RGB).'''
def denoise(img, isRgb=False):
    if isRgb:
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    cv.normalize(img, img, 0, 165, cv.NORM_MINMAX)
    img = cv.bitwise_not(img)
    _, img = cv.threshold(img, 255, 0, cv.THRESH_TRUNC)
    _, img = cv.threshold(img, 127, 0, cv.THRESH_TOZERO)
    img = cv.bitwise_not(img)
    img = cv.fastNlMeansDenoising(img, None, 20, 7, 21)
    if isRgb:
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
    return img

def denoise_at(path, isRgb=False):
    return denoise(cv.imread(path, cv.IMREAD_GRAYSCALE), isRgb)

if __name__ == "__main__":
    cv.imshow('output', denoise_at('/Users/kyle/Desktop/test.png'))
    cv.waitKey(0)
    cv.destroyAllWindows()
    cv.waitKey(1)
