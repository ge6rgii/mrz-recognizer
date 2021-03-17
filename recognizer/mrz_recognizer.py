import numpy as np
import cv2
import imutils


class ImageProcessor:

    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
    sq_kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))

    @staticmethod
    def _resize_image(image, maxsize):
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
        image = self._resize_image(image, maxsize=700)
        return self._find_mrz_contours(image)


class DataParser:

    def __init__(self, countries_codes: dict) -> None:
        self.countries_codes = countries_codes

    @staticmethod
    def _clean_the_strings(mrz_raw: str) -> list:
        mrz_string = mrz_raw.replace(' ', '').replace('\x0c', '')
        return list(filter(lambda x: x, mrz_string.split('\n')))
        
    @staticmethod    
    def _get_personal_name(mrz_string: str) -> list:
        mrz_data = list(filter(lambda x: x, mrz_string.split('<')))
        full_name = list(map(lambda x: x.capitalize(), mrz_data))
        return ' '.join(full_name)

    @staticmethod
    def _get_sex(raw_string: str) -> str:
        if raw_string == 'M':
            return 'Male'
        return 'Female'

    @staticmethod
    def _birth_date_parser(date_string: str) -> str:
        year = date_string[:2]
        month = date_string[2:4]
        day = date_string[4:6]

        if int(year) < 21:
            year = '20' + year
        else:
            year = '19' + year
        
        date_string = '.'.join([day, month, year])
        return date_string

    def _get_country_name(self, code: str) -> str:
        try:
            return self.countries_codes[code]
        except KeyError:
            return ''

    def _get_personal_data(self, line_1: str, line_2: str) -> dict:
        self.country_code = line_1[2:5]
        pass_num, personal_data = line_2.split(self.country_code)

        self.pass_num     = pass_num[:-1].replace('<', '')
        self.sex          = self._get_sex(personal_data[7:8])
        self.birth_date   = self._birth_date_parser(personal_data[:6])
        self.country      = self._get_country_name(self.country_code)
        self.name         = self._get_personal_name(line_1[5:])

        return {
            "country_code": self.country_code,
            "country": self.country,
            "name": self.name,
            "pass_num": self.pass_num,
            "sex": self.sex,
            "birth_date": self.birth_date
            }

    def get_data(self, mrz_raw: str) -> dict:
        """Work in progress."""
        line_1, line_2 = self._clean_the_strings(mrz_raw.upper())

        # TODO: meditate on how to:
        # get date of issue; split names and surnames.
        if line_1[0] == 'P':
            return self._get_personal_data(line_1, line_2)
