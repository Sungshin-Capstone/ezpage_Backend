
from rest_framework import generics, permissions
from .models import Expense
from .serializers import ExpenseSerializer
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .serializers import ScanResultExpenseSerializer

class ScanResultExpenseCreateView(generics.CreateAPIView):
    serializer_class = ScanResultExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, manual_input=False)

# 1) 수동 지출 추가
class ExpenseCreateView(generics.CreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# 2) 여행별 지출 목록 조회
class ExpenseListByTripView(generics.ListAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        trip_id = self.kwargs['trip_id']
        # 예시: description 필드에 "trip:1" 같은 식으로 trip_id 포함시켜 연결하는 경우
        return Expense.objects.filter(user=self.request.user, description__icontains=f"trip:{trip_id}").order_by('-date')

# 3) 날짜별 지출 목록 조회
class ExpenseListByDateView(generics.ListAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        date_str = self.request.query_params.get('date')
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        return Expense.objects.filter(user=self.request.user, date=date_obj).order_by('-created_at')
