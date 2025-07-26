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
