# expenses/views/payment_guide_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Wallet, Trip, Expense
from ..payment_guide import IntegratedPaymentSystem

class PaymentGuideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 요청 데이터 검증
            trip_id = request.data.get('trip_id')
            amount = request.data.get('amount')
            currency_code = request.data.get('currency')

            if not all([trip_id, amount, currency_code]):
                return Response(
                    {"error": "여행 ID, 금액, 화폐 코드는 필수 입력값입니다."},
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
            result = system.process_transaction(currency_code, amount, wallet_dict)

            # IntegratedPaymentSystem에서 에러가 반환된 경우 처리
            if "error" in result:
                 return Response(result, status=status.HTTP_400_BAD_REQUEST)

            # 결과에 추가 정보 포함
            result.update({
                "trip_id": trip_id,
                "requested_currency": currency_code,
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
                {"error": f"결제 가이드 처리 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MenuPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 요청 데이터 검증
            trip_id = request.data.get('trip_id')
            menu_data = request.data.get('menu_data')

            if not trip_id or not menu_data:
                return Response(
                    {"error": "여행 ID와 메뉴 데이터는 필수 입력값입니다."},
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

            # 메뉴 데이터 처리
            for menu_item in menu_data:
                # 가격에서 통화 기호와 쉼표 제거
                price_original = menu_item['price_original'].replace('¥', '').replace(',', '')
                price_krw = menu_item['price_krw'].replace('원', '').replace(',', '')
                
                # 지출 내역 저장
                expense = Expense.objects.create(
                    user=request.user,
                    amount=price_original,
                    currency=menu_item['currency'],
                    description=f"{menu_item['menu_ko']} ({menu_item['menu_original']})",
                    category='FOOD',
                    is_scan_result=True
                )

                # 지갑 데이터 업데이트
                currency_unit = float(price_original)
                wallet = wallets.filter(currency_unit=currency_unit).first()
                
                if wallet and wallet.quantity > 0:
                    wallet.quantity -= 1
                    wallet.save()

            return Response({
                "message": "메뉴 결제가 완료되었습니다.",
                "menu_data": menu_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"메뉴 결제 처리 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
