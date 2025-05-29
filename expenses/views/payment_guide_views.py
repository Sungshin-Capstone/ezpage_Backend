# expenses/views/payment_guide_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..payment_guide import IntegratedPaymentSystem

class PaymentGuideAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        country_code = request.data.get("country_code")
        food_price = request.data.get("food_price")
        wallet = request.data.get("wallet")

        if not (country_code and food_price and wallet):
            return Response({"error": "필수 데이터가 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        system = IntegratedPaymentSystem()
        result = system.process_transaction(country_code, food_price, wallet)

        return Response(result, status=status.HTTP_200_OK)

class PaymentGuideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 요청 데이터에서 필요한 정보 추출
            amount = request.data.get('amount')
            currency = request.data.get('currency')
            
            if not amount or not currency:
                return Response(
                    {"error": "금액과 통화는 필수 입력값입니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 통화별 권장 지폐/동전 구성 계산
            currency_guides = {
                "KRW": {
                    "notes": [50000, 10000, 5000, 1000],
                    "coins": [500, 100, 50, 10],
                    "unit": "원"
                },
                "JPY": {
                    "notes": [10000, 5000, 2000, 1000],
                    "coins": [500, 100, 50, 10, 5, 1],
                    "unit": "엔"
                },
                "USD": {
                    "notes": [100, 50, 20, 10, 5, 1],
                    "coins": [0.25, 0.10, 0.05, 0.01],
                    "unit": "달러"
                },
                "EUR": {
                    "notes": [500, 200, 100, 50, 20, 10, 5],
                    "coins": [2, 1, 0.50, 0.20, 0.10, 0.05, 0.02, 0.01],
                    "unit": "유로"
                }
            }

            # 선택된 통화에 대한 가이드 가져오기
            currency_guide = currency_guides.get(currency, currency_guides["KRW"])
            
            # 금액을 정수로 변환
            amount_int = int(float(amount))
            
            # 지폐/동전 구성 계산
            payment_breakdown = []
            remaining = amount_int
            
            # 지폐 계산
            for note in currency_guide["notes"]:
                if remaining >= note:
                    count = remaining // note
                    payment_breakdown.append({
                        "type": "note",
                        "value": note,
                        "count": count,
                        "total": note * count
                    })
                    remaining -= note * count
            
            # 동전 계산
            for coin in currency_guide["coins"]:
                coin_value = int(coin * 100) if isinstance(coin, float) else coin
                if remaining >= coin_value:
                    count = remaining // coin_value
                    payment_breakdown.append({
                        "type": "coin",
                        "value": coin,
                        "count": count,
                        "total": coin_value * count
                    })
                    remaining -= coin_value * count

            # 가이드 응답 생성
            guide = {
                "amount": amount,
                "currency": currency,
                "unit": currency_guide["unit"],
                "payment_breakdown": payment_breakdown,
                "tips": [
                    f"총 {amount}{currency_guide['unit']}를 지불하실 때 위와 같이 준비하시면 됩니다.",
                    "거스름돈을 받을 때는 지폐와 동전을 잘 확인하세요."
                ]
            }

            return Response(guide, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
