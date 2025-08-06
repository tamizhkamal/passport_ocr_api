from concurrent.futures import ThreadPoolExecutor
import os
from PIL import Image
import pytesseract
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ocr_utils import extract_passport_data
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from logging_config import setup_logging
import logging
from deep_translator import GoogleTranslator
import os
from .utils.translate_utils import translate_key_to_english, translate_key_to_arabic
import tempfile
from rest_framework.views import APIView
from passporteye import read_mrz
from deep_translator import GoogleTranslator
from datetime import datetime
import re




pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'


setup_logging()
logger = logging.getLogger(__name__)

logger.info("Logging started!")


class PassportOCRView(APIView):
    def post(self, request):
        uploaded_file = request.FILES.get("passport_image")

        # Set Tesseract path (once)
        os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'


        if not uploaded_file:
            return Response({"error": "passport_image is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid image file", "details": str(e)}, status=400)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file, format="JPEG")
            temp_path = temp_file.name

        # Arabic OCR
        original_flag = os.environ.get("TESSERACT_OCT", "")
        try:
            os.environ["TESSERACT_OCT"] = "true"
            arabic_data = extract_passport_data(image)

            os.environ["TESSERACT_OCT"] = "false"
            english_data = extract_passport_data(image)
        finally:
            os.environ["TESSERACT_OCT"] = original_flag

        result = {}
        all_keys = set(english_data.keys()) | set(arabic_data.keys())

        for key in all_keys:
            en_val = str(english_data.get(key, "") or "").strip()
            ar_val = str(arabic_data.get(key, "") or "").strip()

            translated_ar_key = translate_key_to_english(key)
            translated_en_key = translate_key_to_arabic(key)

            similarity = difflib.SequenceMatcher(None, en_val.lower(), ar_val.lower()).ratio()

            result[key] = {
                "english_value": en_val,
                "arabic_value": ar_val,
                "similarity": round(similarity, 2),
                "english_field": translated_en_key,
                "arabic_field": translated_ar_key,
                "match": en_val.lower() == ar_val.lower()
            }

        return Response({
            "comparison_result": result,
            "note": "Arabic ↔ English OCR verification completed"
        }, status=status.HTTP_200_OK)
    
class UploadMultipleImageFilesView(APIView):
    def post(self, request):
        # Get multiple uploaded files
        image_files = request.FILES.getlist('passport_image')

        if not image_files:
            return Response({'error': 'passport_files is required'}, status=status.HTTP_400_BAD_REQUEST)

        extracted_results = []

        for index, image_file in enumerate(image_files):
            try:
                image = Image.open(image_file)

                logger.info(f"[{index}] Image uploaded and opened successfully")

                # Extract data from image
                text_data = extract_passport_data(image)
                extracted_results.append({
                    'index': index,
                    'status': 'success',
                    'extracted_data': text_data
                })

            except Exception as e:
                logger.error(f"[{index}] Failed to process image: {str(e)}")
                extracted_results.append({
                    'index': index,
                    'status': 'error',
                    'message': str(e)
                })

        logger.info("All uploaded image files processed")
        return Response({'results': extracted_results}, status=status.HTTP_200_OK)    


import base64
import io
from PIL import Image  # Pillow library
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from members.ocr_utils import extract_passport_data
import difflib
import os

class ComparePassportOCRView(APIView):
    def post(self, request, *args, **kwargs):
        print("Received request to OCR comparison")

        passport_file = request.FILES.get("passport_image")

        if not passport_file:
            return Response(
                {"error": "passport_image is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = Image.open(passport_file)
        except Exception as e:
            return Response(
                {"error": "Uploaded file is not a valid image", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract using two different OCR engines (Dummy examples below)
        original_flag = os.environ.get("TESSERACT_OCT", "")
        try:
            os.environ["TESSERACT_OCT"] = "true"
            tesseract_data = extract_passport_data(image)

            os.environ["TESSERACT_OCT"] = "false"
            passporteye_data = extract_passport_data(image)
        finally:
            os.environ["TESSERACT_OCT"] = original_flag

        # Compare fields
        comparison = {}
        all_keys = set(tesseract_data.keys()) | set(passporteye_data.keys())
        for key in all_keys:
            val1 = str(tesseract_data.get(key, "")).strip()
            val2 = str(passporteye_data.get(key, "")).strip()
            is_match = val1.lower() == val2.lower()
            similarity = difflib.SequenceMatcher(None, val1, val2).ratio()
            comparison[key] = {
                "ocr_date_1": val1,
                "ocr_date_2": val2,
                "match": is_match,
                "similarity": round(similarity, 2)
            }

        return Response({"comparison_result": comparison}, status=status.HTTP_200_OK)


def normalize_data(input_data, to_lang="en"):
    """Convert all keys to English-standard for uniform comparison"""
    normalized = {}
    for key, value in input_data.items():
        if to_lang == "en":
            normalized_key = translate_key_to_english(key)
        else:
            normalized_key = translate_key_to_arabic(key)
        normalized[normalized_key] = value
    return normalized



class CrossLanguagePassportCompareAPIView(APIView):
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("passport_image")
        # print(uploaded_file,"<---------------------------------- uploaded_file")
        if not uploaded_file:
            return Response({"error": "passport_image is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid image file", "details": str(e)}, status=400)


        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file, format="JPEG")
            temp_path = temp_file.name


        # Extract Arabic and English separately using env flags (mocking logic)
        original_flag = os.environ.get("TESSERACT_OCT", "")
        try:
            os.environ["TESSERACT_OCT"] = "true"
            arabic_data = extract_passport_data(image)

            os.environ["TESSERACT_OCT"] = "false"
            english_data = extract_passport_data(image)
        finally:
            os.environ["TESSERACT_OCT"] = original_flag

        # Main comparison result
        result = {}

        all_keys = set(english_data.keys()) | set(arabic_data.keys())

        for key in all_keys:
            en_val = str(english_data.get(key, "") or "").strip()
            ar_val = str(arabic_data.get(key, "") or "").strip()

            translated_ar_key = translate_key_to_english(key)
            translated_en_key = translate_key_to_arabic(key)

            similarity = difflib.SequenceMatcher(None, en_val.lower(), ar_val.lower()).ratio()

            result[key] = {
                "english_value": en_val,
                "arabic_value": ar_val,
                "similarity": round(similarity, 2),
                "english_field": translated_en_key,
                "arabic_field": translated_ar_key,
                "match": en_val.lower() == ar_val.lower()
            }

        return Response({
            "comparison_result": result,
            "note": "Arabic ↔ English OCR verification completed"
        }, status=status.HTTP_200_OK)


class CrossLanguage_Passport_CompareAPIView(APIView):
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("passport_image")

        if not uploaded_file:
            return Response({"error": "passport_image is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert uploaded file to RGB image
            image = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid image file", "details": str(e)}, status=400)

        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG")
                temp_path = temp_file.name

            # ✅ Set Tesseract path (optional: adjust path if needed)
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
            os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'

            # ✅ Extract MRZ
            mrz = read_mrz(temp_path)
            mrz_data = mrz.to_dict() if mrz else {}

            english_name = ""
            if mrz_data:
                given_names = mrz_data.get("names", "")
                surname = mrz_data.get("surname", "")
                english_name = f"{given_names} {surname}".strip()

            # ✅ Arabic OCR using pytesseract
            arabic_text = pytesseract.image_to_string(image, lang='ara', config='--psm 6').strip()

            # ✅ Simple keyword search
            arabic_keywords = ["الاسم", "اسم", "اللقب"]
            arabic_name_found = any(keyword in arabic_text for keyword in arabic_keywords)

            # ✅ Final response
            result = {
                "english_mrz_data": mrz_data,
                "arabic_text": arabic_text,
                "english_name_extracted": english_name,
                "arabic_keyword_found": arabic_name_found,
                "comparison_status": "Matched" if english_name and arabic_name_found else "Mismatch or Not Found"
            }

            return Response(result, status=200)

        except Exception as e:
            return Response({"error": "Processing failed", "details": str(e)}, status=500)



# class Overall_CompareAPIView(APIView):
#     def post(self, request, *args, **kwargs):
#         base64_image = request.data.get("images_base64")

#         if not base64_image:
#             return Response({"error": "images_base64 is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Clean and decode base64 image
#             if "," in base64_image:
#                 base64_image = base64_image.split(",")[1]
#             image_data = base64.b64decode(base64_image)
#             image = Image.open(io.BytesIO(image_data)).convert("RGB")
#         except Exception as e:
#             return Response({"error": "Invalid base64 image", "details": str(e)}, status=400)

#         try:
#             # Save to temp file
#             with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
#                 image.save(temp_file, format="JPEG")
#                 temp_path = temp_file.name

#             # 1. MRZ extraction (using passporteye)
#             mrz_obj = read_mrz(temp_path)
#             mrz_data = mrz_obj.to_dict() if mrz_obj else {}

#             # 2. Arabic text OCR
#             arabic_text = pytesseract.image_to_string(image, lang="ara").strip()

#             # 3. Translation (Arabic to English)
#             translated_text = GoogleTranslator(source='ar', target='en').translate(arabic_text)

#             result = {
#                 "mrz_data": mrz_data,
#                 "passporteye_raw_data": str(mrz_obj) if mrz_obj else None,
#                 "arabic_ocr_text": arabic_text,
#                 "translated_english_text": translated_text,
#             }

#             return Response(result, status=200)

#         except Exception as e:
#             return Response({"error": "Processing failed", "details": str(e)}, status=500)


def format_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%y%m%d")
        if dt.year > datetime.now().year:
            dt = dt.replace(year=dt.year - 100)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str


def parse_passporteye_object(mrz_obj, address=None):
    if not mrz_obj:
        return None

    result = {}
    for k, v in mrz_obj.__dict__.items():
        if not k.startswith("_"):
            if k in ["date_of_birth", "expiration_date"] and isinstance(v, str):
                result[k] = format_date(v)
            else:
                result[k] = v

    if address:
        result["arabic_address"] = address

    return result


def extract_probable_arabic_address(arabic_text):
    lines = arabic_text.split('\n')
    address_candidates = []

    for line in lines:
        line = line.strip()
        if len(line) >= 8 and re.search(r'\d', line) and re.search(r'[\u0600-\u06FF]', line):
            address_candidates.append(line)

    return address_candidates[0] if address_candidates else None


class Overall_CompareAPIView(APIView):
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("passport_image")
        print(uploaded_file, "<---------------------------------- uploaded_file")

        if not uploaded_file:
            return Response({"error": "passport_image is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Set Tesseract path (optional if already in environment)
        os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'

        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid image file", "details": str(e)}, status=400)

        try:
            # Save temp image for MRZ
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG")
                temp_path = temp_file.name

            # ✅ 1. MRZ Extraction
            mrz_obj = read_mrz(temp_path)
            mrz_data = mrz_obj.to_dict() if mrz_obj else {}

            if "date_of_birth" in mrz_data:
                mrz_data["date_of_birth"] = format_date(mrz_data["date_of_birth"])
            if "expiration_date" in mrz_data:
                mrz_data["expiration_date"] = format_date(mrz_data["expiration_date"])

            # ✅ 2. Arabic OCR using Tesseract
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # adjust if needed
            arabic_text = pytesseract.image_to_string(image, lang='ara', config='--psm 6').strip()

            # ✅ 3. Translate Arabic to English
            translated_text = ""
            if arabic_text:
                translated_text = GoogleTranslator(source='ar', target='en').translate(arabic_text)

            # ✅ 4. Extract Arabic Address
            address_line = extract_probable_arabic_address(arabic_text)

            # ✅ 5. Final response
            result = {
                "mrz_data": {
                    **mrz_data,
                    "arabic_address": address_line
                },
                "passporteye_data": parse_passporteye_object(mrz_obj, address=address_line),
                "arabic_ocr_text": arabic_text,
                "translated_english_text": translated_text
            }

            return Response(result, status=200)

        except Exception as e:
            return Response({"error": "Processing failed", "details": str(e)}, status=500)
        


class MergedPassportCompareAPIView(APIView):
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("passport_image")
        if not uploaded_file:
            return Response({"error": "passport_image is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid image file", "details": str(e)}, status=400)

        # ✅ Step 1: Arabic OCR using Tesseract
        try:
            arabic_text = pytesseract.image_to_string(image, lang='ara', config='--psm 6').strip()
        except Exception as e:
            arabic_text = ""
            print("Arabic OCR failed:", e)

        # ✅ Step 2: Translation (if needed)
        translated_text = ""
        if request.query_params.get("translate", "true").lower() == "true" and arabic_text:
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(GoogleTranslator(source='ar', target='en').translate, arabic_text)
                    translated_text = future.result(timeout=5)
            except Exception as e:
                translated_text = "Translation failed: " + str(e)

        # ✅ Step 3: OCR Field Extraction
        try:
            english_data = extract_passport_data(image)
            arabic_data = {}  # No structured arabic field extraction
        except Exception as e:
            return Response({"error": "Field extraction failed", "details": str(e)}, status=500)

        # ✅ Step 4: Compare Fields
        comparison_result = {}
        all_keys = set(english_data.keys()) | set(arabic_data.keys())
        for key in all_keys:
            en_val = str(english_data.get(key, "") or "").strip()
            ar_val = str(arabic_data.get(key, "") or "").strip()

            translated_ar_key = translate_key_to_english(key)
            translated_en_key = translate_key_to_arabic(key)

            similarity = difflib.SequenceMatcher(None, en_val.lower(), ar_val.lower()).ratio()

            comparison_result[key] = {
                "english_value": en_val,
                "arabic_value": ar_val,
                "similarity": round(similarity, 2),
                "english_field": translated_en_key,
                "arabic_field": translated_ar_key,
                "match": en_val.lower() == ar_val.lower()
            }

        # ✅ Step 5: MRZ Extraction
        try:
            buf = io.BytesIO()
            image.save(buf, format="JPEG")
            buf.seek(0)

            mrz_obj = read_mrz(buf)
            mrz_data = mrz_obj.to_dict() if mrz_obj else {}

            if "date_of_birth" in mrz_data:
                mrz_data["date_of_birth"] = format_date(mrz_data["date_of_birth"])
            if "expiration_date" in mrz_data:
                mrz_data["expiration_date"] = format_date(mrz_data["expiration_date"])

            address_line = extract_probable_arabic_address(arabic_text)

        except Exception as e:
            return Response({"error": "MRZ or address processing failed", "details": str(e)}, status=500)

        # ✅ Step 6: Final Response
        final_result = {
            "mrz_data": {
                **mrz_data,
                "arabic_address": address_line
            },
            "OCR_data": parse_passporteye_object(mrz_obj, address=address_line),
            "comparison_result": comparison_result,
            "arabic_ocr_text": arabic_text,
            "translated_english_text": translated_text
        }

        return Response(final_result, status=200)
