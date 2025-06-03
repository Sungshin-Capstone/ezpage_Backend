# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from ..models import Wallet, Trip
from ..serializers import WalletSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class WalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trip_id = request.query_params.get('trip_id')
        if not trip_id:
            return Response(
                {"error": "여행 ID가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
            wallets = Wallet.objects.filter(user=request.user, trip=trip)
            
            if not wallets.exists():
                return Response(
                    {"error": "해당 여행에 대한 지갑을 찾을 수 없습니다."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 모든 지갑의 total_amount 합산
            total_amount = sum(wallet.total_amount for wallet in wallets)
            
            return Response({
                'message': '지갑 총액 조회 성공',
                'total_amount': float(total_amount),
                'currency_symbol': self._get_currency_symbol(wallets.first().country_code)
            })
            
        except Trip.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 여행입니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _calculate_wallet_total(self, wallet):
        """지갑의 총 금액 계산"""
        total = Decimal('0')
        wallet_dict = wallet.get_wallet_dict()
        
        for denomination, quantity in wallet_dict.items():
            total += Decimal(str(denomination)) * Decimal(str(quantity))
        
        return float(total)
    
    def _get_currency_symbol(self, country_code):
        """국가 코드에 따른 화폐 기호 반환"""
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
        trip_id = request.data.get("trip_id")
        detected = request.data.get("detected", {})

        if not trip_id or not detected:
            return Response({"error": "여행 ID와 감지된 화폐 정보(detected)가 필요합니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            trip = Trip.objects.get(id=trip_id, user=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "존재하지 않는 여행입니다."}, status=status.HTTP_404_NOT_FOUND)

        saved_items = {}
        for key, quantity in detected.items():
            parts = key.split("_")
            if len(parts) != 2 or quantity <= 0:
                continue

            currency_code, unit_with_suffix = parts
            unit_str = ''.join(filter(str.isdigit, unit_with_suffix))
            if not unit_str:
                continue

            currency_unit = Decimal(unit_str)
            country_code = self._get_country_code(currency_code)
            if not country_code:
                continue

            wallet, _ = Wallet.objects.get_or_create(
                user=request.user,
                trip=trip,
                currency_unit=currency_unit,
                defaults={
                    "country_code": country_code,
                    "currency_code": currency_code,
                    "quantity": 0
                }
            )
            
            # add_quantity 메서드를 사용하거나 직접 누적
            wallet.quantity += quantity
            wallet.save()
            saved_items[key] = quantity

        # Calculate and update total wallet amount for the trip
        total_amount = Decimal('0')
        wallets_for_trip = Wallet.objects.filter(user=request.user, trip=trip)
        for wallet in wallets_for_trip:
             total_amount += Decimal(str(wallet.currency_unit)) * Decimal(str(wallet.quantity))
        
        trip.total_wallet_amount = total_amount
        trip.save()

        if saved_items:
            return Response({"message": "지갑에 감지된 화폐 정보가 저장되었습니다.", "saved_items": saved_items, "total_wallet_amount": float(total_amount)}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "감지된 화폐 정보가 없습니다.", "saved_items": {}, "total_wallet_amount": float(total_amount)}, status=status.HTTP_200_OK)

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
                
                # 응답에 총액 정보 추가
                response_data = serializer.data
                response_data['wallet_total'] = self._calculate_wallet_total(updated_wallet)
                response_data['currency_symbol'] = self._get_currency_symbol(updated_wallet.country_code)
                
                return Response(response_data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Wallet.DoesNotExist:
            return Response({"error": "지갑을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    
    def _calculate_wallet_total(self, wallet):
        """지갑의 총 금액 계산"""
        total = Decimal('0')
        wallet_dict = wallet.get_wallet_dict()
        
        for denomination, quantity in wallet_dict.items():
            total += Decimal(str(denomination)) * Decimal(str(quantity))
        
        return float(total)
    
    def _get_currency_symbol(self, country_code):
        """국가 코드에 따른 화폐 기호 반환"""
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
            
            # 차감 전 총액 계산
            before_total = Decimal('0')
            for wallet in wallets:
                before_total += Decimal(str(self._calculate_wallet_total(wallet)))
            
            # 차감 가능 여부 확인
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
            
            # Process deductions
            for deduction in deductions:
                currency_unit = deduction.get('currency_unit')
                quantity = deduction.get('quantity')
                if currency_unit and quantity:
                    wallet = wallets.filter(currency_unit=currency_unit).first()
                    if wallet:
                        # Update wallet balance
                        wallet.update_balance(currency_unit, -quantity)
            
            # 차감 후 총액 계산
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
            return Response(
                {"error": "존재하지 않는 여행입니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"차감 처리 중 오류가 발생했습니다: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_wallet_total(self, wallet):
        """지갑의 총 금액 계산"""
        total = Decimal('0')
        wallet_dict = wallet.get_wallet_dict()
        
        for denomination, quantity in wallet_dict.items():
            total += Decimal(str(denomination)) * Decimal(str(quantity))
        
        return float(total)
    
    def _get_currency_symbol(self, country_code):
        """국가 코드에 따른 화폐 기호 반환"""
        currency_symbols = {
            'US': '$',
            'CN': '¥',
            'JP': '¥',
            'KR': '₩'
        }
        return currency_symbols.get(country_code, '$')