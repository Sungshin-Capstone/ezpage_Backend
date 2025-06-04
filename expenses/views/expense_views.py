from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Expense
from ..serializers import ExpenseSerializer
from decimal import Decimal


class ExpenseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExpenseListByTripView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        expenses = Expense.objects.filter(trip_id=trip_id, user=request.user)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

class ExpenseListByDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.query_params.get('date')
        if not date:
            return Response(
                {"error": "날짜를 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expenses = Expense.objects.filter(date=date, user=request.user)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

class ScanResultExpenseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
    

class GuideExpenseDeductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        trip_id = request.data.get("trip_id")
        currency = request.data.get("currency")
        total_price_original = Decimal(str(request.data.get("total_price_original", 0)))
        total_price_krw = Decimal(str(request.data.get("total_price_krw", 0)))
        menu_items = request.data.get("menu_items", [])

        if not trip_id or not menu_items:
            return Response({"error": "여행 ID와 메뉴 정보가 필요합니다."}, status=400)

        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
            wallets = Wallet.objects.filter(user=request.user, trip=trip, currency_code=currency)
            if not wallets.exists():
                return Response({"error": "해당 통화의 지갑이 없습니다."}, status=404)

            # 총합 차감
            before_total = sum(w.total_amount for w in wallets)
            before_krw = sum(w.converted_total_krw for w in wallets)

            for wallet in wallets:
                wallet.total_amount -= total_price_original
                wallet.converted_total_krw -= total_price_krw
                wallet.save()

            # 지출 데이터 저장
            saved_expense_ids = []
            for item in menu_items:
                expense = Expense.objects.create(
                    user=request.user,
                    trip=trip,
                    currency=currency,
                    amount=Decimal(str(item["price_original"])),
                    description=item["menu_ko"],
                    manual_input=False,
                    is_scan_result=True,
                    date=timezone.now().date()
                )
                saved_expense_ids.append(expense.id)

            after_total = sum(w.total_amount for w in wallets)
            after_krw = sum(w.converted_total_krw for w in wallets)

            return Response({
                "message": "지출 저장 및 지갑 차감이 완료되었습니다.",
                "saved_expenses": saved_expense_ids,
                "before_total_amount": float(before_total),
                "after_total_amount": float(after_total),
                "before_converted_total_krw": float(before_krw),
                "after_converted_total_krw": float(after_krw)
            })
        except Trip.DoesNotExist:
            return Response({"error": "해당 여행이 존재하지 않습니다."}, status=404)
