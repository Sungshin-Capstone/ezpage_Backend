from django.urls import path
from .views import ReceiptScanView, CurrencyScanView

urlpatterns = [
    path('receipt/', ReceiptScanView.as_view(), name='scan-receipt'),
    path('currency/', CurrencyScanView.as_view(), name='scan-currency'),
]
