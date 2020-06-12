import cv2 as cv

from denoise.denoise import denoise
from template_matching.template_matching import template_matching


def main():
    input = "INPUT IMAGE"
    denoised_image = denoise(input)
    template_matched_image = template_matching(denoised_image)

    cv.namedWindow('output', cv.WINDOW_NORMAL)
    cv.resizeWindow('output', 1100, 1100)
    cv.imshow('output', template_matching('/Users/kyle/Desktop/input.jpeg'))
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
