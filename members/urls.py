from django.urls import path
from .views import PassportOCRView, UploadMultipleBase64ImagesView

urlpatterns = [
    path('passport-ocr/', PassportOCRView.as_view(), name='passport-ocr'),
    path('upload-multiple-base64/', UploadMultipleBase64ImagesView.as_view(), name='upload-multiple-base64'),
]
