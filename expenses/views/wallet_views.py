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
            
            # 모든 지갑의 정보를 합산
            total_amount = Decimal('0')
            wallet_details = []
            
            for wallet in wallets:
                wallet_total = self._calculate_wallet_total(wallet)
                total_amount += Decimal(str(wallet_total))
                
                wallet_data = WalletSerializer(wallet).data
                wallet_data['wallet_total'] = wallet_total
                wallet_data['currency_symbol'] = self._get_currency_symbol(wallet.country_code)
                wallet_details.append(wallet_data)
            
            return Response({
                'wallets': wallet_details,
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
        # 프론트에서 JSON 데이터를 request.data에서 직접 받아옵니다.
        # 필요한 데이터는 trip_id와 detected 딕셔너리입니다.
        trip_id = request.data.get("trip_id")
        detected = request.data.get("detected", {})
        
        # 필요한 데이터(trip_id, detected)가 있는지 확인
        if not trip_id or not detected:
            return Response(
                {"error": "여행 ID와 감지된 화폐 정보(detected)가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        from ..models import Wallet, Trip
        try:
            # 요청한 사용자의 해당 여행 정보를 가져옵니다.
            trip = Trip.objects.get(id=trip_id, user=request.user)
        except Trip.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 여행입니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # detected 데이터를 순회하며 지갑에 저장하거나 수량을 누적합니다.
        # detected 예시: {"USD_5dollar": 1, "USD_20dollar": 1}
        saved_items = {}
        for key, quantity in detected.items():
            # 화폐 정보 파싱 (예: "USD_5dollar" -> unit=5, code="USD", country="US")
            currency_unit = None
            country_code = None
            currency_code = None

            # 예시 파싱: USD_단위dollar 형태
            if "_dollar" in key:
                parts = key.split("_")
                if len(parts) == 2:
                    code_part, unit_part = parts
                    if code_part == "USD":
                        currency_code = "USD"
                        country_code = "US" # USD의 국가 코드
                        try:
                            currency_unit = float(unit_part.replace("dollar", ""))
                        except ValueError:
                            currency_unit = None # 숫자 변환 실패

            # TODO: 필요시 다른 화폐 단위 (KRW_단위won, JPY_단위yen, CNY_단위yuan 등) 파싱 로직 추가
            # 예: elif "_won" in key: ...
            # 예: elif "_yen" in key: ...

            # 유효한 화폐 정보이고 수량이 0보다 큰 경우에만 처리
            if currency_unit is not None and country_code is not None and currency_code is not None and quantity > 0:
                 # 같은 여행, 같은 화폐 단위의 지갑이 있으면 가져오고, 없으면 새로 생성합니다.
                 # get_or_create는 unique_together = ('user', 'trip', 'currency_unit') 기준으로 동작합니다.
                wallet, created = Wallet.objects.get_or_create(
                    user=request.user,
                    trip=trip,
                    currency_unit=currency_unit,
                    defaults={
                        "country_code": country_code, 
                        "currency_code": currency_code, 
                        "quantity": 0 # 새로 생성 시 초기 수량은 0
                    }
                )
                # 기존 지갑이거나 새로 생성된 지갑에 수량을 누적합니다.
                # Wallet 모델에 add_quantity 메서드가 구현되어 있어야 합니다.
                try:
                    wallet.add_quantity(quantity)
                    saved_items[key] = quantity # 성공적으로 처리된 항목 기록
                except Exception as e:
                    # 누적 중 오류 발생 시 (예: add_quantity 문제)
                    print(f"Error adding quantity to wallet {wallet.id}: {e}")
                    # 필요에 따라 에러 로깅 또는 응답에 포함

        # 성공 응답 반환
        # 실제로 저장된 항목 목록을 포함하여 프론트에 알려줄 수 있습니다.
        if saved_items:
             return Response(
                {
                    "message": "지갑에 감지된 화폐 정보가 저장되었습니다.",
                    "saved_items": saved_items # 실제로 저장된 항목 목록
                },
                status=status.HTTP_200_OK
            )
        else:
            # detected 데이터가 비어있거나 유효한 항목이 없는 경우
            return Response(
                 {
                    "message": "감지된 화폐 정보가 없습니다.",
                    "saved_items": {} 
                 },
                 status=status.HTTP_200_OK # 또는 status.HTTP_204_NO_CONTENT
            )

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