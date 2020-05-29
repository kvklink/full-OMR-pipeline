import cv2 as cv

img_color = cv.imread('/Users/kyle/Desktop/test.png')
img_gray = cv.cvtColor(img_color, cv.COLOR_BGR2GRAY)
cv.normalize(img_gray,  img_gray, 0, 165, cv.NORM_MINMAX)

# is dit netjes?
img_gray = cv.bitwise_not(img_gray)
# nee
_, img_gray = cv.threshold(img_gray, 255, 0, cv.THRESH_TRUNC)
_, img = cv.threshold(img_gray, 127, 0, cv.THRESH_TOZERO)
# werkt het?
img = cv.bitwise_not(img)
# ja
dst = cv.fastNlMeansDenoising(img, None, 20, 7, 21)


# cv.imwrite("/home/karel/Desktop/output.jpg", dst)

# cv.imshow('input', img_color)
# cv.waitKey(0)
# cv.destroyAllWindows()
# cv.waitKey(1)
#
# cv.imshow('grayscale', img_gray)
# cv.waitKey(0)
# cv.destroyAllWindows()
# cv.waitKey(1)
#
# cv.imshow('truncated', img)
# cv.waitKey(0)
# cv.destroyAllWindows()
# cv.waitKey(1)
#
cv.imshow('output', dst)
cv.waitKey(0)
cv.destroyAllWindows()
cv.waitKey(1)
