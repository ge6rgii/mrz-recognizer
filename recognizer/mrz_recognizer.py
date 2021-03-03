import numpy as np
import cv2
import imutils


class ImageProcessor:

    def __init__(self):
        self.rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        self.sq_kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))

    @staticmethod
    def _resize_image(image, maxsize=700):
        height = image.shape[0]
        width = image.shape[1]
        if height > width:
            ratio = width / height
            new_shape = int(maxsize * ratio), maxsize
            return cv2.resize(image, new_shape)

        ratio = height / width
        new_shape = maxsize, int(maxsize * ratio)

        return cv2.resize(image, new_shape)

    def _find_the_right_contour(self, cnts, image):
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            ar = w / float(h)
            crWidth = w / float(image.shape[1])

            if ar > 5 and crWidth > 0.5:
                pX = int((x + w) * 0.03)
                pY = int((y + h) * 0.03)
                (x, y) = (x - pX, y - pY)
                (w, h) = (w + (pX * 2), h + (pY * 2))
                mrz_area = image[y:y + h, x:x + w]

                return mrz_area

    def _find_mrz_contours(self, image):
        """
        I will split this madness into separate methods.
        Someday.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0) # Not sure that it's necessary.
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, self.rect_kernel)

        gradX = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        gradX = np.absolute(gradX)
        minVal, maxVal = np.min(gradX), np.max(gradX)
        gradX = (255 * ((gradX - minVal) / (maxVal - minVal))).astype("uint8")
        gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, self.rect_kernel)

        gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, self.rect_kernel)
        threshold = cv2.threshold(gradX, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        threshold = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, self.sq_kernel)
        threshold = cv2.erode(threshold, None, iterations=4)

        p = int(image.shape[1] * 0.05)
        threshold[:, 0:p] = 0
        threshold[:, image.shape[1] - p:] = 0

        cnts = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

        roi = self._find_the_right_contour(cnts, image)
        return roi

    def get_mrz_area(self, path):
        image = cv2.imread(path)
        image = self._resize_image(image)
        return self._find_mrz_contours(image)

class DataParser:
    """
    Todo: meditate on how to parse the mrz lines
    from different countries passports.
    """

    @staticmethod
    def _clean_the_strings(mrz_raw: list) -> list:
        mrz_data = list(filter(lambda x: x, mrz_raw.split('<')))
        return list(map(lambda x: x.replace('\n', '').replace('\x0c', ''), mrz_data))
