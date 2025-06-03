from django.urls import path
from .views.expense_views import (
    ExpenseCreateView,
    ExpenseListByTripView,
    ExpenseListByDateView,
    ScanResultExpenseCreateView,
)
from .views.trip_views import (
    TripListCreateView,
    TripDetailView,
)
from .views.wallet_views import (
    WalletSummaryView,
    WalletScanResultView,
    WalletUpdateView,
    WalletDeductView,
)
from .views.payment_guide_views import PaymentGuideView, MenuPaymentView

urlpatterns = [
    # Expense endpoints
    path('expenses/', ExpenseCreateView.as_view(), name='expense-create'),
    path('expenses/<int:trip_id>/', ExpenseListByTripView.as_view(), name='expense-list-trip'),
    path('expenses/date/', ExpenseListByDateView.as_view(), name='expense-list-date'),
    path('expenses/scan-result/', ScanResultExpenseCreateView.as_view(), name='expense-scan-result'),
    
    # Trip endpoints
    path('trips/', TripListCreateView.as_view(), name='trip-list-create'),
    path('trips/<int:pk>/', TripDetailView.as_view(), name='trip-detail'),
    
    # Wallet endpoints
    path('wallet/', WalletSummaryView.as_view(), name='wallet-summary'),
    path('wallet/scan-result/', WalletScanResultView.as_view(), name='wallet-scan-result'),
    path('wallet/<int:pk>/update/', WalletUpdateView.as_view(), name='wallet-update'),
    path('wallet/deduct/', WalletDeductView.as_view(), name='wallet-deduct'),
    
    # Payment Guide endpoints
    path('expenses/payment_guide/', PaymentGuideView.as_view(), name='payment-guide'),
    path('expenses/menu_payment/', MenuPaymentView.as_view(), name='menu-payment'),
]