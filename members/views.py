import base64
from io import BytesIO
from urllib import request
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PassportBase64ImageSerializer
from .ocr_utils import extract_passport_data

class PassportOCRView(APIView):
    def post(self, request):
        # print("Received request data:", request.data)
        # Validate the request data using the serializer
        serializer = PassportBase64ImageSerializer(data=request.data)
        # print(serializer.is_valid(),"--------------------------------------------> serializer.is_valid()")
        # print(request.data)
        print(type(request.data['image_base64']))

        if serializer.is_valid():
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
            return Response({"extracted_data": text_data})
        
        print(serializer.errors, "--------------------------------------------> serializer.errors")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
