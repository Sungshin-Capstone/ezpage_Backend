from rest_framework import serializers
from .models import Expense

class ExpenseFromScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            'trip', 'date', 'time',
            'item_name', 'amount', 'currency', 'amount_krw'
        ]
