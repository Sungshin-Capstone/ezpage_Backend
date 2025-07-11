from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from django.utils import timezone
from ..models import Wallet, Trip
from ..serializers import WalletSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class WalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trip_id = request.query_params.get('trip_id')
        if not trip_id:
            return Response({"error": "여행 ID가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
            wallets = Wallet.objects.filter(user=request.user, trip=trip)
            if not wallets.exists():
                return Response({"error": "해당 여행에 대한 지갑 정보가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

            total_amount = sum((w.total_amount or Decimal('0')) for w in wallets)
            converted_total_krw = sum((w.converted_total_krw or Decimal('0')) for w in wallets if w.denominations)
            currency_code = wallets.first().currency_code if wallets.exists() else None
            currency_symbol = self._get_currency_symbol(currency_code)

            currency_details = {}
            for w in wallets:
                # Ensure denominations is treated as a dictionary
                wallet_denominations = w.denominations if isinstance(w.denominations, dict) else {}
                if wallet_denominations:
                    for unit, qty in wallet_denominations.items():
                         currency_details[f"{w.currency_code}_{unit}dollar"] = qty

            return Response({
                "trip_id": trip.id,
                "user_id": trip.user.id,
                "total_amount": float(total_amount),
                "currency_symbol": currency_symbol,
                "converted_total_krw": float(converted_total_krw),
                "converted_currency_symbol": "₩",
                "currency_details": currency_details
            }, status=status.HTTP_200_OK)

        except Trip.DoesNotExist:
            return Response({"error": "존재하지 않는 여행입니다."}, status=status.HTTP_404_NOT_FOUND)



    def _calculate_wallet_total(self, wallet):
        total = Decimal('0')
        wallet_dict = wallet.get_wallet_dict()
        for denomination, quantity in wallet_dict.items():
            total += Decimal(str(denomination)) * Decimal(str(quantity))
        return float(total)

    
    def _get_currency_symbol(self, country_code):
        currency_symbols = {
            'US': '$',
            'CN': '¥',
            'JP': '¥',
            'KR': '₩'
        }
        return currency_symbols.get(country_code, '$')

class WalletScanResultView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        total = request.data.get("total")
        currency_symbol = request.data.get("currency_symbol")
        detected = request.data.get("detected", {})
        converted_total_krw = request.data.get("converted_total_krw")

        if (total is None or currency_symbol is None or converted_total_krw is None):
            return Response(
                {"error": "필수 정보가 누락되었습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = timezone.now().date()

        trip_id = request.data.get("trip_id")
        if trip_id:
            trip = Trip.objects.filter(id=trip_id, user=request.user).first()
        else:
            trip = Trip.objects.filter(
                user=request.user,
                start_date__lte=today,
                end_date__gte=today
            ).order_by('start_date').first()


        if not trip:
            return Response(
                {"error": "오늘 날짜에 해당하는 여행이 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        currency_mapping = {
            '$': 'USD',
            '¥': 'JPY',
            '￥': 'CNY',
            '₩': 'KRW'
        }
        currency_code = currency_mapping.get(currency_symbol)
        if not currency_code:
            return Response({"error": "알 수 없는 통화 기호입니다."}, status=400)

        # 이렇게 if문 다음에 실행
        country_code = self._get_country_code(currency_code)

        saved_items = {}
        if detected:
            try:
                wallet = Wallet.objects.filter(user=request.user, trip=trip).first()

                if wallet:
                    if wallet.currency_code != currency_code:
                        return Response(
                            {"error": "이미 등록된 지갑의 통화와 다릅니다. 한 여행에는 하나의 통화만 사용할 수 있습니다."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # 같은 통화 → 기존 값에 합산
                    wallet.total_amount += Decimal(str(total))
                    wallet.converted_total_krw += Decimal(str(converted_total_krw))

                    for denom, qty in detected.items():
                        wallet.denominations[denom] = wallet.denominations.get(denom, 0) + qty

                    wallet.save()
                else:
                    # 새 지갑 생성
                    wallet = Wallet.objects.create(
                        user=request.user,
                        trip=trip,
                        currency_code=currency_code,
                        country_code=country_code,
                        total_amount=Decimal(str(total)),
                        converted_total_krw=Decimal(str(converted_total_krw)),
                        denominations=detected
                    )
            except Exception as e:
                return Response({"error": "지갑 저장 중 오류", "detail": str(e)}, status=400)

            for key, quantity in detected.items():
                if quantity <= 0:
                    continue
                saved_items[key] = quantity

        try:
            trip.total_wallet_amount = Decimal(str(total))
            trip.converted_total_krw = Decimal(str(converted_total_krw))
            trip.save()
        except (ValueError, TypeError):
            return Response(
                {"error": "총 금액 형식이 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "message": "지갑에 감지된 화폐 정보가 저장되었습니다.",
            "trip_id": trip.id,
            "user_id": trip.user.id,
            "saved_items": saved_items,
            "total_amount": float(total),
            "currency_symbol": currency_symbol,
            "converted_total_krw": float(converted_total_krw),
            "currency_code": currency_code,
            "country_code": country_code
        }, status=status.HTTP_200_OK)

    def _get_country_code(self, currency_code):
        return {
            "USD": "US",
            "KRW": "KR",
            "JPY": "JP",
            "CNY": "CN"
        }.get(currency_code, None)

class WalletUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            wallet = Wallet.objects.get(pk=pk, user=request.user)
            serializer = WalletSerializer(wallet, data=request.data, partial=True)
            if serializer.is_valid():
                updated_wallet = serializer.save()
                response_data = serializer.data
                response_data['wallet_total'] = self._calculate_wallet_total(updated_wallet)
                response_data['currency_symbol'] = self._get_currency_symbol(updated_wallet.country_code)
                return Response(response_data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Wallet.DoesNotExist:
            return Response({"error": "지갑을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    
    def _calculate_wallet_total(self, wallet):
        total = Decimal('0')
        wallet_dict = wallet.get_wallet_dict()
        for denomination, quantity in wallet_dict.items():
            total += Decimal(str(denomination)) * Decimal(str(quantity))
        return float(total)
    
    def _get_currency_symbol(self, country_code):
        currency_symbols = {
            'US': '$',
            'CN': '¥',
            'JP': '¥', 
            'KR': '₩'
        }
        return currency_symbols.get(country_code, '$')

class WalletDeductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        trip_id = request.data.get("trip_id")
        deduct_amount = request.data.get("deduct_amount")
        deduct_amount_krw = request.data.get("deduct_amount_krw")

        if not trip_id or deduct_amount is None or deduct_amount_krw is None:
            return Response(
                {"error": "여행 ID, 차감 금액, 환산 금액이 모두 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            trip = Trip.objects.get(pk=trip_id, user=request.user)
            wallets = Wallet.objects.filter(user=request.user, trip=trip)
            if not wallets.exists():
                return Response(
                    {"error": "해당 여행에 대한 지갑 정보가 없습니다."},
                    status=status.HTTP_404_NOT_FOUND
                )

            before_total_amount = sum((w.total_amount or Decimal("0")) for w in wallets)
            before_converted_total_krw = sum((w.converted_total_krw or Decimal("0")) for w in wallets)

            after_total_amount = before_total_amount - Decimal(str(deduct_amount))
            after_converted_total_krw = before_converted_total_krw - Decimal(str(deduct_amount_krw))

            # 차감 적용
            for wallet in wallets:
                if wallet.total_amount:
                    wallet.total_amount = max(wallet.total_amount - Decimal(str(deduct_amount)), Decimal("0"))
                if wallet.converted_total_krw:
                    wallet.converted_total_krw = max(wallet.converted_total_krw - Decimal(str(deduct_amount_krw)), Decimal("0"))
                wallet.save()

            return Response({
                "message": "지갑에서 금액이 차감되었습니다.",
                "before_total_amount": float(before_total_amount),
                "before_converted_total_krw": float(before_converted_total_krw),
                "deduct_amount": float(deduct_amount),
                "deduct_amount_krw": float(deduct_amount_krw),
                "after_total_amount": float(after_total_amount),
                "after_converted_total_krw": float(after_converted_total_krw),
                "currency_symbol": self._get_currency_symbol(wallets.first().country_code),
                "converted_currency_symbol": "₩"
            }, status=status.HTTP_200_OK)

        except Trip.DoesNotExist:
            return Response({"error": "존재하지 않는 여행입니다."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"차감 처리 중 오류가 발생했습니다: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_currency_symbol(self, country_code):
        currency_symbols = {
            'US': '$',
            'CN': '¥',
            'JP': '¥',
            'KR': '₩'
        }
        return currency_symbols.get(country_code, '$')