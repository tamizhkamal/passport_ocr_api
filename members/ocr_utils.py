# utils.py
import os
import platform
import tempfile
import logging
import pytesseract
from members.utils.extract_passport_passport_eye import extract_using_passporteye
from members.utils.extract_using_tesseract import extract_using_tesseract

from logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Set Tesseract path on Windows
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_passport_data(passport_file):
    """
    Extracts data from a passport image using either Tesseract or PassportEye,
    based on the TESSERACT_OCT environment variable.
    """

    # Save the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        if hasattr(passport_file, 'chunks'):
            for chunk in passport_file.chunks():
                tmp.write(chunk)
        else:
            passport_file.save(tmp, format='PNG')
        temp_file_path = tmp.name

    # Check which OCR method to use
    use_tesseract = os.getenv("TESSERACT_OCT", "False").lower() == "true"

    # if use_tesseract:
    #     logger.info("🔍 Using Tesseract OCR for passport data extraction")
    #     return extract_using_tesseract(temp_file_path)
    # else:
    logger.info("📸 Using PassportEye OCR for passport data extraction")
    return extract_using_passporteye(temp_file_path)
