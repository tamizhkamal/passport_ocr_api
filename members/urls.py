from django.urls import path
from .views import ComparePassportOCRView, CrossLanguage_Passport_CompareAPIView, CrossLanguagePassportCompareAPIView, MergedPassportCompareAPIView, Overall_CompareAPIView, PassportOCRView, UploadMultipleImageFilesView

urlpatterns = [
    path('passport-ocr/', PassportOCRView.as_view(), name='passport-ocr'),
    path('upload-multiple-image/', UploadMultipleImageFilesView.as_view(), name='upload-multiple-base64'),
    path("compare-passport-ocr/", ComparePassportOCRView.as_view(), name="compare_passport_ocr"),
    path('passport-compare-crosslang/', CrossLanguagePassportCompareAPIView.as_view(), name='passport-compare-crosslang'),
    path('passport_compare_cross_lang/', CrossLanguage_Passport_CompareAPIView.as_view(), name='passport-compare'),
    path('Overall_api/', Overall_CompareAPIView.as_view(), name='overall-passport-compare'),
    path('passport-merged-compare/', MergedPassportCompareAPIView.as_view(), name='passport-merged-compare'),  # 👈 New route
]
