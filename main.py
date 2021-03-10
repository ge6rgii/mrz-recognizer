from recognizer import ImageProcessor, DataParser
from pytesseract import image_to_string

processor = ImageProcessor()
mrz_area = processor.get_mrz_area("dataset/RUS1.jpg")
mrz_string = image_to_string(mrz_area, lang="sabrina")
