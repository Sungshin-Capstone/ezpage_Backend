from django.urls import path
from .views import (
    ExpenseCreateView,
    ExpenseListByTripView,
    ExpenseListByDateView,
    ScanResultExpenseCreateView  # 이거 추가 !!!
)

urlpatterns = [
    path('create/', ExpenseCreateView.as_view(), name='expense-create'),             # 그냥 create/
    path('<int:trip_id>/', ExpenseListByTripView.as_view(), name='expense-list-trip'), # 그냥 <trip_id>/
    path('', ExpenseListByDateView.as_view(), name='expense-list-date'),               # 그냥 빈 문자열 ''
    path('scan-result/', ScanResultExpenseCreateView.as_view(), name='expense-scan-result'), # 그냥 scan-result/
]
