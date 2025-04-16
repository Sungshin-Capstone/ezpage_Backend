from django.urls import path
from .views import ReceiptScanView, CurrencyScanView, ImageUploadAPIView

urlpatterns = [
    path('receipt/', ReceiptScanView.as_view(), name='scan-receipt'),
    path('currency/', CurrencyScanView.as_view(), name='scan-currency'),
    path('receipt/', ImageUploadAPIView.as_view()),
]
