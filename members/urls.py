from django.urls import path
from .views import PassportOCRView

urlpatterns = [
    path('passport-ocr/', PassportOCRView.as_view(), name='passport-ocr'),
]
