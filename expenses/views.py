
from rest_framework import generics, permissions
from rest_framework import serializers
from .models import Expense,Wallet,Trip
from .serializers import ExpenseSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from .serializers import ScanResultExpenseSerializer
from .serializers import WalletScanResultSerializer
from .serializers import TripSerializer
from .serializers import WalletUpdateSerializer
from .serializers import WalletDeductSerializer
from rest_framework.generics import RetrieveUpdateDestroyAPIView

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

class WalletScanResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        wallets = Wallet.objects.filter(user=user).order_by('-created_at')
        serializer = WalletScanResultSerializer(wallets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WalletScanResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trip_id = request.query_params.get('trip_id')
        user = request.user

        try:
            trip = Trip.objects.get(id=trip_id, user=user)
        except Trip.DoesNotExist:
            return Response({"error": "해당 여행을 찾을 수 없습니다."}, status=404)

        wallet_qs = Wallet.objects.filter(user=user, trip=trip, quantity__gt=0).order_by('-currency_unit')
        total_amount = sum(w.currency_unit * w.quantity for w in wallet_qs)

        wallet_data = [
            {"currency_unit": w.currency_unit, "quantity": w.quantity}
            for w in wallet_qs
        ]

        expenses_qs = Expense.objects.filter(user=user, date__range=[trip.start_date, trip.end_date]).order_by('-date', '-created_at')
        expenses_data = [
            {
                "date": e.date.strftime("%Y-%m-%d"),
                "time": e.created_at.strftime("%H:%M"),
                "description": e.description,
                "amount": int(e.amount)
            }
            for e in expenses_qs
        ]

        return Response({
            "total_amount": total_amount,
            "wallet": wallet_data,
            "expenses": expenses_data
        })

class WalletUpdateView(generics.UpdateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

class WalletDeductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletDeductSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            trip_id = serializer.validated_data['trip_id']
            deductions = serializer.validated_data['deductions']

            try:
                trip = Trip.objects.get(id=trip_id, user=user)
            except Trip.DoesNotExist:
                return Response({"error": "여행 정보를 찾을 수 없습니다."}, status=404)

            errors = []
            for item in deductions:
                unit = item['currency_unit']
                qty = item['quantity']

                try:
                    wallet = Wallet.objects.get(user=user, trip=trip, currency_unit=unit)
                    if wallet.quantity < qty:
                        errors.append(f"{unit} 단위 화폐가 부족합니다.")
                    else:
                        wallet.quantity -= qty
                        wallet.save()
                except Wallet.DoesNotExist:
                    errors.append(f"{unit} 단위 화폐를 소지하고 있지 않습니다.")

            if errors:
                return Response({"errors": errors}, status=400)

            return Response({"message": "차감 완료"}, status=200)
        else:
            return Response(serializer.errors, status=400)

class TripCreateView(generics.CreateAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TripDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'