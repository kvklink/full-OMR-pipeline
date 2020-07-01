import cv2


class Template:
    def __init__(self, name: str, image, height_units: float = 1):
        self.image = cv2.imread(image, 0) if isinstance(image, str) else image
        self.name = name
        self.height_units = height_units
        self.h = self.image.shape[0]
        self.w = self.image.shape[1]

    def update_size(self, tup):
        self.h, self.w = tup
