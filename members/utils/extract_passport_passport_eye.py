import cv2
import pytesseract
import re
import pycountry
from passporteye import read_mrz
from datetime import datetime

from logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

def extract_using_passporteye(temp_file_path, passport_file=None):
    print("📸 Using PassportEye OCR")
    mrz_data = extract_mrz_from_image(temp_file_path)
    print("MRZ Data:", mrz_data, "<------------ MRZ Extraction Output")


    extract_custom_fields_from_passport(temp_file_path)

    # Initialize fields
    passport_data = {
        "fullname": f"{mrz_data.get('names', '')} {mrz_data.get('surname', '')}".strip(),
        "surname": mrz_data.get('surname'),
        "middleName": None,
        "fatherName": None,
        "spouseName": None,
        "mothername": None,
        "placeOfBirth": None,
        "placeOfIssue": None,
        "passportType": mrz_data.get('mrz_type'),
        "country": mrz_data.get('country'),
        "passportNo": mrz_data.get('number'),
        "nationality": mrz_data.get('nationality'),
        "maritalStatus": None,
        "sex": mrz_data.get('sex'),
        "dateOfBirth": parse_mrz_date(mrz_data.get('date_of_birth')),
        "address": None,
        "profession": None,
        "dateOfExpiry": parse_mrz_date(mrz_data.get('expiration_date')),
        "dateOfIssue": None,
        "footerText": mrz_data.get('raw_text')
    }

    # ---------------- OCR using Tesseract ----------------
    image = cv2.imread(temp_file_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    image_rgb = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)

    filename_lower = passport_file.name.lower() if passport_file and hasattr(passport_file, 'name') else ""
    possible_arabic_countries = ["jordan", "syria", "iran", "iraq", "lebanon", "egypt", "saudi", "yemen"]
    ocr_lang = "eng+ara+fas" if any(keyword in filename_lower for keyword in possible_arabic_countries) else "eng"
    print(f"🔤 OCR Language: {ocr_lang}")

    raw_text = pytesseract.image_to_string(image_rgb, lang=ocr_lang)
    print("📝 OCR Raw Text:\n", raw_text)

    # Normalize text
    text = raw_text.replace('\n', ' ').replace('\x0c', ' ')
    text = re.sub(r'\s+', ' ', text)
    text_upper = raw_text.upper()

    # ---------------- Extract Additional Fields ----------------
    passport_data['address'] = extract_clean_address(text)
    # Place of Birth
   # Use original raw OCR text with newlines
    # --- Step-by-step OCR line scan ---
    raw_lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    lines_upper = [line.upper() for line in raw_lines]
    
    place_of_birth = None
    place_of_issue = None
    
    for i, line in enumerate(lines_upper):
        # Match: PLACE OF BIRTH - city,state format (Ex: NERGUNAM,TAMIL RADU)
        if not place_of_birth and re.match(r'^[A-Z\s]+,\s*[A-Z\s]+$', line):
            place_of_birth = line.title()

            # Try next line as Place of Issue
            if i + 1 < len(lines_upper):
                next_line = lines_upper[i + 1].strip()
                # Make sure it's not same as PoB and is all uppercase
                if (
                    next_line.upper() != line
                    and next_line.isupper()
                    and 5 <= len(next_line) <= 30
                    and not re.search(r'[^A-Z]', next_line)
                ):
                    place_of_issue = next_line.title()
            break  # Stop after first match

    # Assign if not already present
    if not passport_data.get("placeOfBirth") and place_of_birth:
        passport_data["placeOfBirth"] = place_of_birth

    if not passport_data.get("placeOfIssue") and place_of_issue:
        passport_data["placeOfIssue"] = place_of_issue

    # Father Name & Mother Name (from capital words)
    lines = text.splitlines()
    cap_words = [line.strip() for line in lines if line.isupper() and len(line.strip()) >= 3]

    if not passport_data['fatherName'] and len(cap_words) >= 1:
        passport_data['fatherName'] = cap_words[0].title()

    if not passport_data['mothername'] and len(cap_words) >= 2:
        passport_data['mothername'] = cap_words[1].title()
    
    logger.info("PassportEye + Tesseract OCR Extraction Complete")
    return passport_data


def extract_mrz_from_image(image_path):
    mrz = read_mrz(image_path)
    if mrz is None:
        return {}
    return mrz.to_dict()


def parse_mrz_date(mrz_date):
    try:
        return datetime.strptime(mrz_date, "%y%m%d").strftime("%Y-%m-%d")
    except:
        return None


def extract_clean_address(text):
    print("Extracting address from text:", text)
    lines = text.splitlines()
    full_text = " ".join([line.strip() for line in lines if line.strip()])

    countries = [c.name.upper() for c in pycountry.countries]
    country_regex = '|'.join(re.escape(c) for c in countries)

    match = re.search(
        r'([A-Z0-9\/,\-\s“”"\'\.]*PIN[:\s]?\d{5,6},\s?[A-Z\s]+,\s?(?:' + country_regex + r'))',
        full_text, re.IGNORECASE
    )

    if match:
        address = match.group(1)
        address = re.sub(r'^.*?(\d{1,}[\w\/,\-\s]*)', r'\1', address)
        address = address.replace("“", '"').replace("”", '"')
        address = re.sub(r'\s+', ' ', address)
        address = re.sub(r',\s*', ', ', address)
        return address.strip().title()

    return None


def extract_field_from_text(text, keywords):
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        for keyword in keywords:
            if keyword.lower() in line.lower():
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    if next_line and len(next_line.split()) <= 4:  # Keep it tight
                        return next_line.title()
    return None


import easyocr

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
        elif 'address' in clean_line or 'mariyamman' in clean_line:  # Address keyword or sample match
            if extracted_info["address"]:
                extracted_info["address"] += " " + line.strip()
            else:
                extracted_info["address"] = line.strip()
    print(extracted_info,"<-------------------------------------------------------------------------------extracted_info")
    return extracted_info
