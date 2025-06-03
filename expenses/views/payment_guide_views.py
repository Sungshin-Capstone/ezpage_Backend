# expenses/views/payment_guide_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Wallet, Trip
from ..payment_guide import IntegratedPaymentSystem

class PaymentGuideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 요청 데이터 검증
            trip_id = request.data.get('trip_id')
            amount = request.data.get('amount')
            country_code = request.data.get('country_code')

            if not all([trip_id, amount, country_code]):
                return Response(
                    {"error": "여행 ID, 금액, 국가 코드는 필수 입력값입니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 금액이 숫자인지 확인
            try:
                amount = float(amount)
            except ValueError:
                return Response(
                    {"error": "금액은 숫자여야 합니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 여행 정보 조회 및 검증
            try:
                trip = Trip.objects.get(id=trip_id, user=request.user)
            except Trip.DoesNotExist:
                return Response(
                    {"error": "존재하지 않는 여행입니다."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 지갑 정보 조회
            wallets = Wallet.objects.filter(user=request.user, trip=trip)
            if not wallets.exists():
                return Response(
                    {"error": "해당 여행에 대한 지갑 정보가 없습니다."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 지갑 데이터를 payment_guide 시스템에 맞는 형식으로 변환
            wallet_dict = {}
            for wallet in wallets:
                wallet_dict[float(wallet.currency_unit)] = wallet.quantity

            # 결제 가이드 처리
            system = IntegratedPaymentSystem()
            result = system.process_transaction(country_code, amount, wallet_dict)

            # 결과에 추가 정보 포함
            result.update({
                "trip_id": trip_id,
                "country_code": country_code,
                "wallet_details": [
                    {
                        "currency_unit": w.currency_unit,
                        "quantity": w.quantity,
                        "total": float(w.currency_unit) * w.quantity
                    }
                    for w in wallets
                ]
            })

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "결제 가이드 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
