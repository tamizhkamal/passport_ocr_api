import base64
from io import BytesIO
import os
from urllib import request
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PassportBase64ImageSerializer
from .ocr_utils import extract_passport_data
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import base64
import uuid
from django.core.files.base import ContentFile
from logging_config import setup_logging
import logging
from deep_translator import GoogleTranslator

setup_logging()
logger = logging.getLogger(__name__)

logger.info("Logging started!")


class PassportOCRView(APIView):
    def post(self, request):
        # print("Received request data:", request.data)
        # Validate the request data using the serializer
        serializer = PassportBase64ImageSerializer(data=request.data)
        # print(serializer.is_valid(),"--------------------------------------------> serializer.is_valid()")
        # print(request.data)
        print(type(request.data['image_base64']))

        if serializer.is_valid():
            logger.info("serializer is valid")
            # print(serializer.validated_data, "--------------------------------------------> serializer.validated_data")
            image_data = serializer.validated_data['image_base64']
            
            # Decode base64 to image
            try:
                image_data = image_data.split(',')[-1]  # remove "data:image/png;base64,"
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
            except Exception as e:
                return Response({'error': 'Invalid image format'}, status=status.HTTP_400_BAD_REQUEST)
            # Extract text from the image
            print(image, "--------------------------------------------> image")
            text_data = extract_passport_data(image)
            logger.success("Passport data extracted successfully")
            return Response({"extracted_data": text_data})
        logger.error("Failed to extract passport data")
        print(serializer.errors, "--------------------------------------------> serializer.errors")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UploadMultipleBase64ImagesView(APIView):
    def post(self, request):
        images_data = request.data.get('images_base64', [])
        logger.info("Received request data for multiple images")
        if not isinstance(images_data, list):
            return Response({'error': 'images_base64 should be a list'}, status=status.HTTP_400_BAD_REQUEST)

        extracted_results = []

        for index, image_base64 in enumerate(images_data):
            try:
                base64_str = image_base64.split(',')[-1]  # remove data:image/jpeg;base64,...
                image_bytes = base64.b64decode(base64_str)
                image = Image.open(BytesIO(image_bytes))

                logger.info(f"[{index}] Image decoded successfully")

                # Extract data from image
                text_data = extract_passport_data(image)
                extracted_results.append({
                    'index': index,
                    'status': 'success',
                    'extracted_data': text_data
                })
                logging.info(f"[{index}] Data extracted successfully")

            except Exception as e:
                logger.error(f"[{index}] Failed to decode image: {str(e)}")
                extracted_results.append({
                    'index': index,
                    'status': 'error',
                    'message': str(e)
                })
        logger.info("All images processed")
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

        base64_image = request.data.get("images_base64")
        passport_file = request.FILES.get("passport_file")  # ✅ uncommented and added back

        print("Received base64_image:", base64_image)

        if not passport_file and not base64_image:
            return Response({"error": "passport_file or images_base64 is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert base64 to PIL.Image
        if base64_image:
            try:
                if "," in base64_image:
                    base64_image = base64_image.split(",")[1]

                image_data = base64.b64decode(base64_image)
                image = Image.open(io.BytesIO(image_data))
                passport_file = image  # Now this is PIL.Image
            except Exception as e:
                return Response({"error": "Invalid base64 image", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif passport_file:
            try:
                image = Image.open(passport_file)
                passport_file = image
            except Exception as e:
                return Response({"error": "Uploaded file is not a valid image", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Now passport_file is PIL.Image — safe to pass
        original_flag = os.environ.get("TESSERACT_OCT", "")
        try:
            os.environ["TESSERACT_OCT"] = "true"
            tesseract_data = extract_passport_data(passport_file)

            os.environ["TESSERACT_OCT"] = "false"
            passporteye_data = extract_passport_data(passport_file)
        finally:
            os.environ["TESSERACT_OCT"] = original_flag

        comparison = {}
        all_keys = set(tesseract_data.keys()) | set(passporteye_data.keys())
        for key in all_keys:
            val1 = str(tesseract_data.get(key, "")).strip()
            val2 = str(passporteye_data.get(key, "")).strip()
            is_match = val1.lower() == val2.lower()
            similarity = difflib.SequenceMatcher(None, val1, val2).ratio()
            comparison[key] = {
                "tesseract": val1,
                "passporteye": val2,
                "match": is_match,
                "similarity": round(similarity, 2)
            }

        return Response({"comparison_result": comparison}, status=status.HTTP_200_OK)

# views.py

import base64
import io
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import difflib

from members.ocr_utils import extract_passport_data
from .utils.translate_utils import translate_key_to_english, translate_key_to_arabic


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
# views.py

class CrossLanguagePassportCompareAPIView(APIView):
    def post(self, request, *args, **kwargs):
        base64_image = request.data.get("images_base64")

        if not base64_image:
            return Response({"error": "images_base64 is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert base64 to PIL.Image
        try:
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            return Response({"error": "Invalid base64 image", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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



import base64
import io
import tempfile
from PIL import Image
import pytesseract
from passporteye import read_mrz
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class CrossLanguage_Passport_CompareAPIView(APIView):
    def post(self, request, *args, **kwargs):
        base64_image = request.data.get("images_base64")

        if not base64_image:
            return Response({"error": "images_base64 is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Strip base64 header if present
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]

            # Decode and convert to image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid base64 image", "details": str(e)}, status=400)

        try:
            # Save image to temp file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG")
                temp_path = temp_file.name

            # MRZ extraction using passporteye
            mrz = read_mrz(temp_path)
            mrz_data = mrz.to_dict() if mrz else {}

            english_name = ""
            if mrz_data:
                given_names = mrz_data.get("names", "")
                surname = mrz_data.get("surname", "")
                english_name = f"{given_names} {surname}".strip()

            # Arabic text extraction using pytesseract
            arabic_text = pytesseract.image_to_string(image, lang="ara").strip()

            # Basic check for Arabic word "name" in text
            arabic_keywords = ["الاسم", "اسم", "اللقب"]  # try to cover more keywords
            arabic_name_found = any(keyword in arabic_text for keyword in arabic_keywords)

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



import base64
import io
import tempfile
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from passporteye import read_mrz
import pytesseract
from deep_translator import GoogleTranslator
from datetime import datetime
import re


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
        base64_image = request.data.get("images_base64")

        if not base64_image:
            return Response({"error": "images_base64 is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid base64 image", "details": str(e)}, status=400)

        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG")
                temp_path = temp_file.name

            # 1. MRZ Extraction
            mrz_obj = read_mrz(temp_path)
            mrz_data = mrz_obj.to_dict() if mrz_obj else {}

            if "date_of_birth" in mrz_data:
                mrz_data["date_of_birth"] = format_date(mrz_data["date_of_birth"])
            if "expiration_date" in mrz_data:
                mrz_data["expiration_date"] = format_date(mrz_data["expiration_date"])

            # 2. Arabic OCR
            arabic_text = pytesseract.image_to_string(image, lang="ara").strip()

            # 3. Translate
            translated_text = GoogleTranslator(source='ar', target='en').translate(arabic_text)

            # 4. Address extraction – NEW logic (no keywords)
            address_line = extract_probable_arabic_address(arabic_text)

            # 5. Final result
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
        base64_image = request.data.get("images_base64")

        if not base64_image:
            return Response({"error": "images_base64 is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Convert image from base64
        try:
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            return Response({"error": "Invalid base64 image", "details": str(e)}, status=400)

        # -----------------------------
        # Step 2: Cross Language Compare
        # -----------------------------
        try:
            # Set env for Arabic OCR
            original_flag = os.environ.get("TESSERACT_OCT", "")
            os.environ["TESSERACT_OCT"] = "true"
            arabic_data = extract_passport_data(image)

            # Set env for English OCR
            os.environ["TESSERACT_OCT"] = "false"
            english_data = extract_passport_data(image)
            os.environ["TESSERACT_OCT"] = original_flag

            # Merge comparison result
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

        except Exception as e:
            return Response({"error": "Cross language OCR failed", "details": str(e)}, status=500)

        # -----------------------------
        # Step 3: MRZ and Arabic OCR block
        # -----------------------------
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG")
                temp_path = temp_file.name

            # MRZ
            mrz_obj = read_mrz(temp_path)
            mrz_data = mrz_obj.to_dict() if mrz_obj else {}

            if "date_of_birth" in mrz_data:
                mrz_data["date_of_birth"] = format_date(mrz_data["date_of_birth"])
            if "expiration_date" in mrz_data:
                mrz_data["expiration_date"] = format_date(mrz_data["expiration_date"])

            # Arabic OCR and translation
            arabic_text = pytesseract.image_to_string(image, lang="ara").strip()
            translated_text = GoogleTranslator(source='ar', target='en').translate(arabic_text)
            address_line = extract_probable_arabic_address(arabic_text)

        except Exception as e:
            return Response({"error": "MRZ or OCR processing failed", "details": str(e)}, status=500)

        # Final merged result
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
