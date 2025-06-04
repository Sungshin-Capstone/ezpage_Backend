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

            total_amount = sum((w.total_amount or Decimal('0')) for w in wallets if w.denominations)
            converted_total_krw = sum((w.converted_total_krw or Decimal('0')) for w in wallets if w.denominations)
            currency_code = wallets.first().currency_code if wallets.exists() else None

            currency_details = {
                f"{w.currency_code}_{w.currency_unit}dollar": w.quantity
                for w in wallets if w.quantity > 0
            }


            return Response({
                "trip_id": trip.id,
                "user_id": trip.user.id,
                "total_amount": float(total_amount),
                "currency_code": currency_code,
                "converted_total_krw": float(converted_total_krw),
                "converted_currency_code": "KRW",
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

        # 오늘 날짜에 포함된 여행 찾기
        today = timezone.now().date()
        trip = Trip.objects.filter(
            user=request.user,
            start_date__lte=today,
            end_date__gte=today
        ).first()

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
        currency_code = currency_mapping.get(currency_symbol, 'USD')
        country_code = self._get_country_code(currency_code)

        Wallet.objects.filter(user=request.user, trip=trip, currency_code=currency_code).delete()

        saved_items = {}
        if detected:
            for key, quantity in detected.items():
                if quantity <= 0:
                    continue
                try:
                    if '_' not in key:
                        continue
                    parts = key.split('_')
                    if len(parts) < 2:
                        continue
                    unit_part = parts[1]
                    unit_str = ''.join(filter(str.isdigit, unit_part))
                    if not unit_str:
                        continue
                    currency_unit = int(unit_str)

                    wallet = Wallet.objects.create(
                        user=request.user,
                        trip=trip,
                        country_code=country_code,
                        currency_code=currency_code,
                        denominations=detected, 
                        converted_total_krw=Decimal(str(converted_total_krw))
                    )
                    saved_items[key] = quantity
                except (ValueError, TypeError):
                    continue

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
        trip_id = request.data.get('trip_id')
        deductions = request.data.get('deductions', [])
        if not trip_id or not deductions:
            return Response(
                {"error": "여행 ID와 차감 정보가 필요합니다."}, 
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

            before_total = Decimal('0')
            for wallet in wallets:
                before_total += Decimal(str(self._calculate_wallet_total(wallet)))
            
            total_deduction = Decimal('0')
            for deduction in deductions:
                currency_unit = Decimal(str(deduction.get('currency_unit', 0)))
                quantity = Decimal(str(deduction.get('quantity', 0)))
                total_deduction += currency_unit * quantity
            
            if total_deduction > before_total:
                return Response(
                    {"error": "차감할 금액이 지갑 잔액을 초과합니다."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            for deduction in deductions:
                currency_unit = deduction.get('currency_unit')
                quantity = deduction.get('quantity')
                if currency_unit and quantity:
                    wallet = wallets.filter(currency_unit=currency_unit).first()
                    if wallet:
                        wallet.update_balance(currency_unit, -quantity)

            after_total = Decimal('0')
            for wallet in wallets:
                after_total += Decimal(str(self._calculate_wallet_total(wallet)))
            
            return Response({
                "message": "지갑에서 금액이 차감되었습니다.",
                "before_total": float(before_total),
                "after_total": float(after_total),
                "deducted_amount": float(before_total - after_total),
                "currency_symbol": self._get_currency_symbol(wallets.first().country_code)
            })
        except Trip.DoesNotExist:
            return Response({"error": "존재하지 않는 여행입니다."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": f"차감 처리 중 오류가 발생했습니다: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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
