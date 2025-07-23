# utils.py

import os
from django.http import JsonResponse
import pytesseract
from PIL import Image
import cv2
import re
import tempfile
import pycountry
import base64
import cv2
import numpy as np
from passporteye import read_mrz
from datetime import datetime

from members.utils.extract_passport_passport_eye import extract_using_passporteye
from members.utils.extract_using_tesseract import extract_using_tesseract


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from logging_config import setup_logging
import logging
setup_logging()
logger = logging.getLogger(__name__)




def extract_passport_data(passport_file):
    # Save the uploaded file to a temporary path
    if hasattr(passport_file, 'chunks'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            for chunk in passport_file.chunks():
                tmp.write(chunk)
            temp_file_path = tmp.name
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            passport_file.save(tmp, format='PNG')
            temp_file_path = tmp.name

    use_tesseract = os.getenv("TESSERACT_OCT", "False").lower() == "true"

    if use_tesseract:
        print("🔍 Using Tesseract OCR")
        logging.info("Using Tesseract OCR for passport data extraction")
        return extract_using_tesseract(passport_file, temp_file_path)
    else:
        print("📸 Using PassportEye OCR")
        logging.info("Using PassportEye OCR for passport data extraction")
        return extract_using_passporteye(temp_file_path)


