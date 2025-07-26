from django.urls import path
from .views import ComparePassportOCRView, CrossLanguagePassportCompareAPIView, PassportOCRView, UploadMultipleBase64ImagesView

urlpatterns = [
    path('passport-ocr/', PassportOCRView.as_view(), name='passport-ocr'),
    path('upload-multiple-base64/', UploadMultipleBase64ImagesView.as_view(), name='upload-multiple-base64'),
    path("compare-passport-ocr/", ComparePassportOCRView.as_view(), name="compare_passport_ocr"),
    path('passport-compare-crosslang/', CrossLanguagePassportCompareAPIView.as_view(), name='passport-compare-crosslang'),
]
