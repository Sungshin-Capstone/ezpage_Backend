from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Wallet, Trip
from ..serializers import WalletSerializer
from django.db import models
from collections import OrderedDict

def add_total_quantity_to_data(data, user):
    from collections import OrderedDict
    from django.db.models import Sum

    # 전체 quantity 합산
    wallets = Wallet.objects.filter(user=user)
    total_quantity = wallets.aggregate(total=Sum('quantity'))['total'] or 0

    # 응답 데이터 순서 지정
    ordered_data = OrderedDict()
    for key in data:
        ordered_data[key] = data[key]
        if key == "trip_id":
            ordered_data["total_quantity"] = total_quantity
    if "trip_id" not in ordered_data:
        ordered_data["total_quantity"] = total_quantity

    return ordered_data

class WalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.filter(user=request.user).first()
        if not wallet:
            return Response({"error": "지갑을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = WalletSerializer(wallet)
        ordered_data = add_total_quantity_to_data(serializer.data, request.user)
        return Response(ordered_data)


class WalletScanResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletSerializer(data=request.data)
        if serializer.is_valid():
            trip_id = request.data.get('trip_id')
            try:
                trip = Trip.objects.get(id=trip_id)
            except Trip.DoesNotExist:
                return Response({'error': '여행(trip)을 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            wallet = serializer.save(user=request.user, trip=trip)
            ordered_data = add_total_quantity_to_data(serializer.data, request.user)
            return Response(ordered_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class WalletUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            wallet = Wallet.objects.get(pk=pk, user=request.user)
            serializer = WalletSerializer(wallet, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Wallet.DoesNotExist:
            return Response({"error": "지갑을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

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
            
            # Process deductions
            for deduction in deductions:
                currency_unit = deduction.get('currency_unit')
                quantity = deduction.get('quantity')
                if currency_unit and quantity:
                    # Update wallet balance
                    wallet.update_balance(currency_unit, -quantity)
            
            return Response({"message": "지갑에서 금액이 차감되었습니다."})
        except (Trip.DoesNotExist, Wallet.DoesNotExist):
            return Response(
                {"error": "여행 또는 지갑을 찾을 수 없습니다."}, 
                status=status.HTTP_404_NOT_FOUND
            ) 