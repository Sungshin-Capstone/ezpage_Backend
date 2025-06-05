from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from django.utils import timezone
from ..models import Expense, Trip, Wallet
from ..serializers import ExpenseSerializer


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
            return Response({"error": "날짜를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
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
        total_price_original = Decimal(str(request.data.get("total_price_original", 0)))
        total_price_krw = Decimal(str(request.data.get("total_price_krw", 0)))
        menu_items = request.data.get("menus", [])

        if not trip_id or not menu_items:
            return Response({"error": "여행 ID와 메뉴 정보가 필요합니다."}, status=400)

        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "해당 여행이 존재하지 않습니다."}, status=404)

        # Get unique currencies from menu items
        currencies = set(item.get("currency") for item in menu_items)
        if not currencies:
            return Response({"error": "메뉴 항목에 통화 정보가 없습니다."}, status=400)

        # Check if all items have the same currency
        if len(currencies) > 1:
            return Response({"error": "모든 메뉴 항목은 동일한 통화를 사용해야 합니다."}, status=400)

        currency = currencies.pop()
        wallets = Wallet.objects.filter(user=request.user, trip=trip, currency_code=currency)
        if not wallets.exists():
            return Response({"error": "해당 통화의 지갑이 없습니다."}, status=404)

        before_total = sum(w.total_amount for w in wallets)
        before_krw = sum(w.converted_total_krw for w in wallets)

        for wallet in wallets:
            wallet.total_amount = (wallet.total_amount or Decimal('0')) - total_price_original
            wallet.converted_total_krw = (wallet.converted_total_krw or Decimal('0')) - total_price_krw
            wallet.save()

        saved_expense_ids = []
        for item in menu_items:
            try:
                currency = item.get("currency")
                price_original = Decimal(str(item.get("price_original", 0)))
                price_krw_str = str(item.get("price_krw", "0")).replace(",", "").replace("원", "")
                price_krw = Decimal(price_krw_str)

                menu_ko = item.get("menu_ko", "")
                menu_original = item.get("menu_original", "")

                expense = Expense.objects.create(
                    user=request.user,
                    trip=trip,
                    currency=currency,
                    amount=price_original,
                    description=menu_ko,
                    manual_input=False,
                    is_scan_result=True,
                    date=timezone.now().date(),
                    category="FOOD"
                )
                saved_expense_ids.append(expense.id)
            except Exception as e:
                return Response({"error": f"지출 항목 저장 중 오류 발생: {str(e)}"}, status=400)

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
