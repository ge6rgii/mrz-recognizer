import numpy as np
import cv2
import imutils


class ImageProcessor:

    def __init__(self):
        self.rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        self.sq_kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    
    @staticmethod
    def _resize(image):
        #height = image.shape[0]
        #width = image.shape[1]
        pass

    def _image_reader(self, path):
        pass

class DataParser:
    pass
