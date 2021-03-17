from recognizer import ImageProcessor, DataParser
from pytesseract import image_to_string
import json
from sys import argv

with open('recognizer/countries_codes.json', 'r') as f:
    countries_codes = json.loads(f.readline())

processor = ImageProcessor()
data_parser = DataParser(countries_codes)

passport = argv[1]
mrz_area = processor.get_mrz_area(f'dataset/{passport}')
mrz_string = image_to_string(mrz_area, lang="sabrina")
print(mrz_string)

# Just some tests.
passport_data = data_parser.get_data(mrz_string)
print(passport_data)
