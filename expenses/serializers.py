# serializers.py

from rest_framework import serializers
from .models import Expense

class ScanResultExpenseSerializer(serializers.ModelSerializer):
    currency = serializers.ChoiceField(choices=["KRW", "JPY", "CNY", "USD", "EUR", "GBP"])

    class Meta:
        model = Expense
        fields = ['id', 'amount', 'currency', 'description']

class ExpenseSerializer(serializers.ModelSerializer):
    currency = serializers.ChoiceField(choices=["KRW", "JPY", "CNY", "USD", "EUR", "GBP"])

    class Meta:
        model = Expense
        fields = ['id', 'user', 'amount', 'currency', 'description', 'manual_input', 'date', 'created_at']
        read_only_fields = ['id', 'user', 'date', 'created_at']
