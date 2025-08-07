from passporteye import read_mrz
from datetime import datetime
from logging_config import setup_logging
import logging
import pytesseract
from PIL import Image
import os

setup_logging()
logger = logging.getLogger(__name__)

# Optional: Setup Tesseract Path
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # Linux
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows

def extract_using_passporteye(temp_file_path):
    print("📸 Using PassportEye OCR + pytesseract")

    # MRZ Extract
    mrz_data = extract_mrz_from_image(temp_file_path)

    # Tesseract OCR
    image = Image.open(temp_file_path).convert("RGB")
    raw_text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')

    extracted_info = extract_custom_fields_from_text(raw_text)

    passport_data = {
        "fullname": f"{mrz_data.get('names', '')} {mrz_data.get('surname', '')}".strip(),
        "surname": mrz_data.get('surname'),
        "middleName": None,
        "fatherName": extracted_info.get("fatherName"),
        "spouseName": None,
        "mothername": extracted_info.get("motherName"),
        "placeOfBirth": None,
        "placeOfIssue": None,
        "passportType": mrz_data.get('mrz_type'),
        "country": mrz_data.get('country'),
        "passportNo": mrz_data.get('number'),
        "nationality": mrz_data.get('nationality'),
        "maritalStatus": None,
        "sex": mrz_data.get('sex'),
        "dateOfBirth": parse_mrz_date(mrz_data.get('date_of_birth')),
        "address": extracted_info.get("address"),
        "profession": None,
        "dateOfExpiry": parse_mrz_date(mrz_data.get('expiration_date')),
        "dateOfIssue": None,
        "footerText": mrz_data.get('raw_text')
    }

    logger.info("PassportEye + pytesseract Extraction Complete ✅")
    return passport_data


def extract_mrz_from_image(image_path):
    mrz = read_mrz(image_path)
    return mrz.to_dict() if mrz else {}


def parse_mrz_date(mrz_date):
    try:
        return datetime.strptime(mrz_date, "%y%m%d").strftime("%Y-%m-%d")
    except:
        return None


def extract_custom_fields_from_text(text):
    extracted_info = {
        "fatherName": None,
        "motherName": None,
        "address": None
    }

    for line in text.splitlines():
        clean_line = line.strip().lower()

        if 'father' in clean_line:
            extracted_info["fatherName"] = line.split(':')[-1].strip()
        elif 'mother' in clean_line:
            extracted_info["motherName"] = line.split(':')[-1].strip()
        elif 'address' in clean_line:
            if extracted_info["address"]:
                extracted_info["address"] += " " + line.strip()
            else:
                extracted_info["address"] = line.strip()

    return extracted_info
