import base64
from io import BytesIO
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