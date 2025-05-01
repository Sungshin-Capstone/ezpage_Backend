from django.urls import path
from .views import (
    ExpenseCreateView,
    ExpenseListByTripView,
    ExpenseListByDateView,
    ScanResultExpenseCreateView,
    WalletScanResultCreateView,
    TripCreateView,
    WalletSummaryView,
    WalletUpdateView,
    WalletDeductView
)

urlpatterns = [
    path('create/', ExpenseCreateView.as_view(), name='expense-create'),
    path('<int:trip_id>/', ExpenseListByTripView.as_view(), name='expense-list-trip'),
    path('', ExpenseListByDateView.as_view(), name='expense-list-date'),
    path('scan-result/', ScanResultExpenseCreateView.as_view(), name='expense-scan-result'),
    path('wallet/scan-result/', WalletScanResultCreateView.as_view(), name='wallet-scan-result'),
    path('trips/', TripCreateView.as_view(), name='trip-create'),
    path('wallet/', WalletSummaryView.as_view(), name='wallet-summary'),
    path('wallet/<int:pk>/update/', WalletUpdateView.as_view(), name='wallet-update'),
    path('wallet/deduct/', WalletDeductView.as_view(), name='wallet-deduct'),
]