from django.urls import path
from .views import ExpenseFromScanView

urlpatterns = [
    path('scan-result/', ExpenseFromScanView.as_view(), name='expense-from-scan'),
]