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
