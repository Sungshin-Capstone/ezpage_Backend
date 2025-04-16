from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


# Create your views here.
class ExpenseFromScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        trip_id = request.data.get("trip")
        items = request.data.get("items", [])
        created_expenses = []

        for item in items:
            expense = Expense.objects.create(
                user=request.user,
                trip_id=trip_id,
                amount=item["amount"],
                currency=item["currency"],
                manual_input=item.get("manual_input", False),
                description=item["name"]
            )
            created_expenses.append({
                "id": expense.id,
                "description": expense.description,
                "amount": expense.amount,
                "currency": expense.currency
            })

        return Response(created_expenses, status=status.HTTP_201_CREATED)
