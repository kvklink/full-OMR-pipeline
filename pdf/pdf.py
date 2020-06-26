from pdf2image import convert_from_path, convert_from_bytes
import cv2 as cv
from PIL import Image

from utils.util import imshow, get_dir

from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)

def toImages(input_path):
    images = convert_from_path(input_path)
    output_dir = get_dir(input_path)
    print(output_dir)
    for i, image in enumerate(images):
        imshow("Image from PDF", image)
        # cv.imwrite(output_dir + "/output i.png", image)
        image.save(output_dir + f"/input {i}.png")
    return

if __name__ == "__main__":
    input_path = 'images/sheets/trombone-full/input.pdf'
    # input_path = 'images/sheets/trombone-full'
    toImages(input_path)