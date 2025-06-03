from django.urls import path
from .views import ReceiptScanView, CurrencyScanView, ImageUploadAPIView, OCRScanView

urlpatterns = [
    path('receipt/', ReceiptScanView.as_view(), name='scan-receipt'),
    path('currency/', CurrencyScanView.as_view(), name='scan-currency'),
    path('receipt/', ImageUploadAPIView.as_view()),
    path("scan/", OCRScanView.as_view(), name="ocr-scan")
]
