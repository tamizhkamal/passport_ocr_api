from passporteye import read_mrz
from datetime import datetime
from logging_config import setup_logging
import logging
import easyocr

setup_logging()
logger = logging.getLogger(__name__)


def extract_using_passporteye(temp_file_path, passport_file=None):
    print("📸 Using PassportEye OCR")
    mrz_data = extract_mrz_from_image(temp_file_path)

    extracted_info = extract_custom_fields_from_passport(temp_file_path)

    # Initialize fields
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

    logger.info("PassportEye + EasyOCR Extraction Complete")
    return passport_data


def extract_mrz_from_image(image_path):
    mrz = read_mrz(image_path)
    return mrz.to_dict() if mrz else {}


def parse_mrz_date(mrz_date):
    try:
        return datetime.strptime(mrz_date, "%y%m%d").strftime("%Y-%m-%d")
    except:
        return None


def extract_custom_fields_from_passport(temp_file_path):
    reader = easyocr.Reader(['en'])
    results = reader.readtext(temp_file_path, detail=0)

    extracted_info = {
        "fatherName": None,
        "motherName": None,
        "address": None
    }

    for line in results:
        clean_line = line.strip().lower()

        if 'father' in clean_line:
            extracted_info["fatherName"] = line.split(':')[-1].strip()
        elif 'mother' in clean_line:
            extracted_info["motherName"] = line.split(':')[-1].strip()
        elif 'address' in clean_line or 'ADDRESS' in clean_line:
            if extracted_info["address"]:
                extracted_info["address"] += " " + line.strip()
            else:
                extracted_info["address"] = line.strip()

    return extracted_info
