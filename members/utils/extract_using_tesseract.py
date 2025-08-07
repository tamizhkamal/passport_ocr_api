# import os
# from django.http import JsonResponse
# import pytesseract
# from PIL import Image
# import cv2
# import re
# import tempfile
# import pycountry
# import base64
# import cv2
# import numpy as np
# from passporteye import read_mrz
# from datetime import datetime
# from logging_config import setup_logging
# import logging
# setup_logging()
# logger = logging.getLogger(__name__)


# def extract_clean_address(text):
#     print("Extracting address from text:", text,"<--------------------------------------------> text")
#     lines = text.splitlines()
#     full_text = " ".join([line.strip() for line in lines if line.strip()])

#     countries = [c.name.upper() for c in pycountry.countries]
#     country_regex = '|'.join(re.escape(c) for c in countries)

#     match = re.search(
#         r'([A-Z0-9\/,\-\s“”"\'\.]*PIN[:\s]?\d{5,6},\s?[A-Z\s]+,\s?(?:' + country_regex + r'))',
#         full_text, re.IGNORECASE
#     )

#     if match:
#         address = match.group(1)
#         address = re.sub(r'^.*?(\d{1,}[\w\/,\-\s]*)', r'\1', address)
#         address = address.replace("“", '"').replace("”", '"')
#         address = re.sub(r'\s+', ' ', address)
#         address = re.sub(r',\s*', ', ', address)
#         return address.strip().title()

#     return None




# def extract_text_from_base64_image(base64_string):
#     try:
#         # Decode base64 to image
#         img_data = base64.b64decode(base64_string)
#         np_array = np.frombuffer(img_data, np.uint8)
#         image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

#         # Preprocess image (optional)
#         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#         # Extract text
#         text = pytesseract.image_to_string(gray)

#         return text.strip()

#     except Exception as e:
#         return f"Error processing image: {str(e)}"




# def extract_using_tesseract(passport_file, temp_file_path):
#     # print("🔍 Using Tesseract OCR")
    
#     image = cv2.imread(temp_file_path)
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#     image_rgb = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)

#     # ✅ Language Detection from File Name
#     filename_lower = passport_file.name.lower() if hasattr(passport_file, 'name') else ""
#     possible_arabic_countries = ["jordan", "syria", "iran", "iraq", "lebanon", "egypt", "saudi", "yemen"]
#     ocr_lang = "eng+ara+fas" if any(keyword in filename_lower for keyword in possible_arabic_countries) else "eng"
#     print(f"🈶 OCR Language: {ocr_lang}")

#     if any(keyword in filename_lower for keyword in possible_arabic_countries):
#         ocr_lang = "eng+ara+fas"  # Arabic + Persian
#         print("🈶 Arabic OCR ENABLED →", ocr_lang)
#     else:
#         print("🔤 English OCR ENABLED")


#     # ✅ OCR with correct language
#     raw_text = pytesseract.image_to_string(image_rgb, lang=ocr_lang)
#     print("----------------------------------------->",raw_text,"<---------------------------------- raw_text")
#     text = raw_text.replace('\n', ' ').replace('\x0c', ' ')
#     text = re.sub(r'\s+', ' ', text)
#     text_upper = raw_text.upper()

#     # Base data format
#     passport_data = {  
#         "fullname": None,
#         "surname": None,
#         "middleName": None,
#         "fatherName": None,
#         "spouseName": None,
#         "mothername": None,
#         "placeOfBirth": None,
#         "placeOfIssue": None,
#         "passportType": None,
#         "country": None,
#         "passportNo": None,
#         "nationality": None,
#         "maritalStatus": None,
#         "sex": None,
#         "dateOfBirth": None,
#         "address": None,
#         "profession": None,
#         "dateOfExpiry": None,
#         "dateOfIssue": None,
#         "footerText": None
#     }
#     match = re.search(r'\b([A-Z]{1,3}\d{6,8})\b', text)
#     passport_data["passportNo"] = match.group(1) if match else None
#     print("PASSPORT NO →", passport_data["passportNo"])

#     # Sex
#     sex = re.search(r'\b(MALE|FEMALE|M|F)\b', text)
#     passport_data['sex'] = sex.group(1)[0] if sex else None

#     # Dates
#     date_ddmmyyyy = re.findall(r'\d{2}/\d{2}/\d{4}', text)
#     date_dd_mmm_yyyy = re.findall(r'\d{2}\s*[A-Za-z]{3}\s*\d{4}', text)
#     all_dates = date_ddmmyyyy + [d.upper() for d in date_dd_mmm_yyyy]

#     passport_data['dateOfBirth'] = all_dates[0] if len(all_dates) > 0 else None
#     passport_data['dateOfIssue'] = all_dates[1] if len(all_dates) > 1 else None
#     passport_data['dateOfExpiry'] = all_dates[2] if len(all_dates) > 2 else None

    
#     # Passport Type + Country Code + Passport Number
#     match_type_line = re.search(r'\b([A-Z])\s+([A-Z]{3})\s+([A-Z0-9]{6,9})\b', text)
#     if match_type_line:
#         passport_data["passportType"] = match_type_line.group(1)  # 'P'
#         passport_data["passportNo"] = match_type_line.group(3)    # 'AKO578443'
#     else:
#         passport_data["passportType"] = None


#     # ✅ Clean dynamic extraction of Place of Issue (like "Government of Kenya")
#     # ✅ Dynamic Place of Issue Extraction
#     # ✅ Improved Dynamic Place of Issue Extraction
#     print("🪵 DEBUG: RAW TEXT LINES ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
#     for line in raw_text.splitlines():
#         print(line)
#     print("🪵 DEBUG END ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑")

#     place_of_issue = None
#     for line in raw_text.splitlines():
#         line_upper = line.strip().upper()
#         if "GOVERNMENT OF" in line_upper:
#             match = re.search(r'GOVERNMENT OF [A-Z ]+', line_upper)
#             if match:
#                 place_of_issue = match.group(0).title()
#                 break

#     passport_data["placeOfIssue"] = place_of_issue



#     if not passport_data["placeOfBirth"]:
#         pob_patterns = [
#             r'Place of Birth[:\s\-]*([A-Z\s]{3,},\s*[A-Z]{3,})',  # English
#             r'Mahall pa Kuzaliwa[:\s\-]*([A-Z\s]{3,},\s*[A-Z]{3,})',  # Swahili
#             r'L[ée]ew de Naissance[:\s\-]*([A-Z\s]{3,},\s*[A-Z]{3,})',  # French variation
#             r'Birth Place[:\s\-]*([A-Z\s]{3,},\s*[A-Z]{3,})',  # Generic fallback
#         ]
        
#         for pattern in pob_patterns:
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match:
#                 passport_data["placeOfBirth"] = match.group(1).strip()
#                 break

#     # Address (cleaned)
#     passport_data['address'] = extract_clean_address(text)

#     # Father / Mother / Place of Birth
#     lines = text.split('\n')
#     joined = " ".join(lines)

#     print("---------------------------------------->",text,"<---------------------------------- text")

#     # ✅ Extract Place of Birth (POB): comes immediately after DOB
#     if passport_data['dateOfBirth']:
#         dob_index = text.find(passport_data['dateOfBirth'])
        
#         # Extract next 50 chars after DOB to catch POB
#         post_dob_text = text[dob_index + 10:dob_index + 60]
        
#         # Look for a capitalized location followed by comma (NERGUNAN, TAMIL NADU)
#         pob_match = re.search(r'\b([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)*),\s*([A-Z\s]+)\b', post_dob_text)
#         print("POB MATCH >>>", pob_match)
#         if pob_match:
#             city = pob_match.group(1)
#             state = pob_match.group(2)
            
#             passport_data['placeOfBirth'] = f"{city}, {state}"
#             print("POB FOUND →", passport_data['placeOfBirth'])
#         else:
#             print("POB NOT FOUND")
    


    
#     # ✅ Ultimate fallback after MRZ for parent names
#     if not passport_data['fatherName'] or not passport_data['mothername']:
#         lines = raw_text.splitlines()

#         # Find MRZ line index
#         mrz_idx = next((i for i, line in enumerate(lines) if line.startswith('P<')), None)

#         if mrz_idx is not None:
#             post_mrz_lines = lines[mrz_idx + 1:]  # lines after MRZ
#         else:
#             post_mrz_lines = lines

#         # Combine and find capitalized names (>= 4 letters)
#         post_text = " ".join(post_mrz_lines)
#         print("POST-MRZ TEXT BLOCK >>>", post_text)

#         cap_words = re.findall(r'\b[A-Z]{4,}\b', post_text)
#         print("FALLBACK UPPERCASE WORDS >>>", cap_words)

#         # Remove known junk
#         skip_words = {'INDIA', 'TAMIL', 'NADU', 'PIN'}
#         cap_words = [w for w in cap_words if w not in skip_words]

#         if not passport_data['fatherName'] and len(cap_words) >= 1:
#             passport_data['fatherName'] = cap_words[0].title()

#         if not passport_data['mothername'] and len(cap_words) >= 2:
#             passport_data['mothername'] = cap_words[1].title()


#     # Country (dynamic)
#     country_found = None
#     for country in pycountry.countries:
#         if country.name.upper() in text.upper():
#             country_found = country.name.upper()
#             break
#     passport_data["country"] = country_found
#     passport_data["nationality"] = country_found

#     # Extract names from MRZ (Machine Readable Zone)
#     lines = raw_text.splitlines()
#     mrz_line = next((line.strip() for line in lines if line.strip().startswith("P<")), None)

#     if mrz_line:
#         print("RAW MRZ >>>", mrz_line)
#         try:
#             # General cleanup
#             mrz_clean = mrz_line.strip()
#             mrz_clean = re.sub(r'[^A-Z<]', '', mrz_clean.upper())  # A-Z and < only

#             # Remove country code
#             if mrz_clean.startswith("P<"):
#                 mrz_clean = mrz_clean[2:]  # remove "P<"

#             # Split into surname and given name
#             parts = mrz_clean.split("<<", 1)
#             if len(parts) == 2:
#                 surname_raw = parts[0].replace("<", " ").strip()
#                 given_raw = parts[1].replace("<", " ").strip()

#                 # Clean given name
#                 given_words = [w for w in given_raw.split() if w.isalpha() and len(w) > 1]
#                 if given_words:
#                     given_name = " ".join(given_words)
#                     passport_data["fullname"] = given_name.title()
#                 else:
#                     passport_data["fullname"] = None

#                 passport_data["surname"] = surname_raw.title()

#                 print("SURNAME →", passport_data["surname"])
#                 print("FULLNAME →", passport_data["fullname"])
#                 dob_raw = mrz_line[13:19]  # YYMMDD
#                 dob = f"19{dob_raw[0:2]}-{dob_raw[2:4]}-{dob_raw[4:6]}"  # Fix year logic as needed
#                 expiry_raw = mrz_line[21:27]
#                 expiry_date = f"20{expiry_raw[0:2]}-{expiry_raw[2:4]}-{expiry_raw[4:6]}"

#                 # data['passport_number'] = passport_number
#                 passport_data['date_of_birth'] = dob
#                 passport_data['expiry_date'] = expiry_date
#                 logger.info("tesseract Extraction Successful")

#         except Exception as e:
#             logger.error("❌ tesseract Name Parse Error: %s", e)

#     logger.info("Passport data extraction completed using Tesseract OCR")
#     return passport_data




# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'



# ------------------------------------------------------------------------------------------------------
from passporteye import read_mrz
import pytesseract
from PIL import Image
import re

def extract_using_tesseract(file_like_object):
    result = {
        "fullname": None,
        "surname": None,
        "middleName": None,
        "fatherName": None,
        "spouseName": None,
        "mothername": None,
        "placeOfBirth": None,
        "placeOfIssue": None,
        "country": None,
        "passportNo": None,
        "nationality": None,
        "maritalStatus": None,
        "sex": None,
        "dateOfBirth": None,
        "address": None,
        "profession": None,
        "dateOfExpiry": None,
        "dateOfIssue": None,
        "footerText": None
    }

    try:
        file_like_object.seek(0)
        mrz = read_mrz(file_like_object)
        if mrz:
            mrz_data = mrz.to_dict()
            result.update({
                "passportNo": mrz_data.get("number", "").replace("<", ""),
                "country": mrz_data.get("country"),
                "nationality": mrz_data.get("nationality"),
                "dateOfBirth": format_mrz_date(mrz_data.get("date_of_birth")),
                "dateOfExpiry": format_mrz_date(mrz_data.get("expiration_date")),
                "sex": mrz_data.get("sex"),
                "surname": mrz_data.get("surname"),
                "fullname": " ".join([mrz_data.get("surname", ""), *mrz_data.get("names", "").split()])
            })
    except Exception as e:
        print("MRZ Extraction Failed:", str(e))

    image = Image.open(file_like_object)
    text = pytesseract.image_to_string(image)
    lines = text.splitlines()
    clean_lines = [l.strip() for l in lines if l.strip()]

    result["placeOfBirth"] = extract_place_of_birth(clean_lines)
    result["placeOfIssue"] = extract_place_of_issue(clean_lines)
    result["fatherName"] = extract_name_nearby(clean_lines, "father")
    result["mothername"] = extract_name_nearby(clean_lines, "mother")
    result["dateOfIssue"] = extract_date(text, r"(?:date of issue|issued on|doi)[:\s\-]*(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4})")
    result["address"] = extract_address_block(text)
    result["footerText"] = extract_footer(text)

    return result


def extract_name_nearby(lines, keyword):
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower():
            match = re.search(rf"{keyword}[:\-]?\s*([A-Z][A-Z\s]+)$", line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and re.match(r"^[A-Z ]{3,}$", next_line):
                    return next_line
    return None

def extract_place_of_birth(lines):
    for i, line in enumerate(lines):
        if "birth" in line.lower():
            match = re.search(r"birth[:\-]?\s*(.*)", line, re.IGNORECASE)
            if match and match.group(1).strip():
                return match.group(1).strip()
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    return next_line
    for line in lines:
        if re.search(r"TAMIL\s+NADU", line, re.IGNORECASE) or "," in line:
            return line
    return None

def extract_place_of_issue(lines):
    for i, line in enumerate(lines):
        if "issue" in line.lower():
            match = re.search(r"issue[:\-]?\s*(.*)", line, re.IGNORECASE)
            if match and match.group(1).strip():
                return match.group(1).strip()
            if i + 1 < len(lines):
                return lines[i + 1].strip()
    for line in reversed(lines):
        cleaned_line = line.strip().replace(":", "")
        if re.match(r"^[A-Z\s]{3,}$", cleaned_line) and len(cleaned_line.split()) <= 2:
            if not re.match(r'^[A-Z]+<', cleaned_line) and not any(
                keyword in cleaned_line.upper() for keyword in ["SURNAME", "GIVEN NAME", "NATIONALITY", "SEX", "DATE", "AUTHORITY"]):
                return cleaned_line.strip()
    return None

def extract_date(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).replace(".", "-").replace("/", "-")
    return None

def format_mrz_date(mrz_date):
    if mrz_date and len(mrz_date) == 6:
        year_prefix = "20" if int(mrz_date[:2]) < 50 else "19"
        year = year_prefix + mrz_date[:2]
        return f"{mrz_date[4:6]}-{mrz_date[2:4]}-{year}"
    return None

def extract_address_block(text):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.search(r"PIN[:\s\-]?\s*\d{6}", line):
            block = lines[max(0, i - 3):i + 1]
            return " ".join([l.strip() for l in block if l.strip()])
    return None

def extract_footer(text):
    lines = text.strip().split('\n')
    footer_lines = lines[-4:]
    mrz_like = [line.strip() for line in footer_lines if "P<" in line or re.match(r"[A-Z0-9<]{20,}", line)]
    return " ".join(mrz_like) if mrz_like else None
