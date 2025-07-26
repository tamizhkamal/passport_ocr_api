# utils/translate_utils.py

arabic_to_english = {
    "الاسم الكامل": "fullname",
    "اسم العائلة": "surname",
    "اسم الأب": "fatherName",
    "اسم الزوج": "spouseName",
    "اسم الأم": "mothername",
    "مكان الولادة": "placeOfBirth",
    "مكان الإصدار": "placeOfIssue",
    "نوع الجواز": "passportType",
    "الدولة": "country",
    "رقم الجواز": "passportNo",
    "الجنسية": "nationality",
    "الحالة الاجتماعية": "maritalStatus",
    "الجنس": "sex",
    "تاريخ الميلاد": "dateOfBirth",
    "العنوان": "address",
    "المهنة": "profession",
    "تاريخ الانتهاء": "dateOfExpiry",
    "تاريخ الإصدار": "dateOfIssue",
    "نص التذييل": "footerText"
}

english_to_arabic = {v: k for k, v in arabic_to_english.items()}

def translate_key_to_english(arabic_key):
    return arabic_to_english.get(arabic_key, arabic_key)

def translate_key_to_arabic(english_key):
    return english_to_arabic.get(english_key, english_key)


import re

def extract_arabic_fields(arabic_text):
    result = {}

    # Example regex or keyword-based search
    name_match = re.search(r'(?<=#ارويوا/ ).{3,30}', arabic_text)
    id_match = re.search(r'\d{9,}', arabic_text)
    dob_match = re.search(r'\d{6}', arabic_text)

    if name_match:
        result["name"] = name_match.group().strip()
    if id_match:
        result["id_number"] = id_match.group().strip()
    if dob_match:
        result["date_of_birth"] = dob_match.group().strip()

    return result
