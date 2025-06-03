# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from ..models import Wallet, Trip
from ..serializers import WalletSerializer

class WalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.filter(user=request.user).first()
        if not wallet:
            return Response({"error": "지갑을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WalletSerializer(wallet)
        data = serializer.data
        
        # 지갑 총액 계산 추가
        data['wallet_total'] = self._calculate_wallet_total(wallet)
        data['currency_symbol'] = self._get_currency_symbol(wallet.country_code)
        
        return Response(data)
    
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

    def post(self, request):
        serializer = WalletSerializer(data=request.data)
        if serializer.is_valid():
            wallet = serializer.save(user=request.user)
            
            # 응답에 총액 정보 추가
            response_data = serializer.data
            response_data['wallet_total'] = self._calculate_wallet_total(wallet)
            response_data['currency_symbol'] = self._get_currency_symbol(wallet.country_code)
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
            wallet = Wallet.objects.get(user=request.user)
            
            # 차감 전 총액 계산
            before_total = self._calculate_wallet_total(wallet)
            
            # Process deductions
            for deduction in deductions:
                currency_unit = deduction.get('currency_unit')
                quantity = deduction.get('quantity')
                if currency_unit and quantity:
                    # Update wallet balance
                    wallet.update_balance(currency_unit, -quantity)
            
            # 차감 후 총액 계산
            after_total = self._calculate_wallet_total(wallet)
            
            return Response({
                "message": "지갑에서 금액이 차감되었습니다.",
                "before_total": before_total,
                "after_total": after_total,
                "deducted_amount": before_total - after_total,
                "currency_symbol": self._get_currency_symbol(wallet.country_code)
            })
        except (Trip.DoesNotExist, Wallet.DoesNotExist):
            return Response(
                {"error": "여행 또는 지갑을 찾을 수 없습니다."}, 
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