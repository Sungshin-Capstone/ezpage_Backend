from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Expense
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
            return Response({"error": "날짜가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        expenses = Expense.objects.filter(date=date, user=request.user)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

class ScanResultExpenseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, is_scan_result=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 