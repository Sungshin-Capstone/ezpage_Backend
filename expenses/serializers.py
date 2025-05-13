# serializers.py

from rest_framework import serializers
from .models import Expense,Wallet,Trip

class ScanResultExpenseSerializer(serializers.ModelSerializer):
    currency = serializers.ChoiceField(choices=["KRW", "JPY", "CNY", "USD", "EUR", "GBP"])

    class Meta:
        model = Expense
        fields = ['id', 'amount', 'currency', 'description']

class ExpenseSerializer(serializers.ModelSerializer):
    currency = serializers.ChoiceField(choices=["KRW", "JPY", "CNY", "USD", "EUR", "GBP"])
    is_scan_result = serializers.BooleanField(required=False, default=False)
    class Meta:
        model = Expense
        fields = ['id', 'user', 'amount', 'currency', 'description', 'manual_input', 'date', 'created_at']
        read_only_fields = ['id', 'user', 'date', 'created_at']

class WalletScanResultSerializer(serializers.ModelSerializer):
    trip_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Wallet
        fields = ['trip_id', 'country_code', 'currency_code', 'currency_unit', 'quantity']

    def create(self, validated_data):
        user = self.context['request'].user
        trip_id = validated_data.pop('trip_id')

        print("🟡 trip_id:", trip_id)
        print("🟡 user:", user)

        try:
            trip = Trip.objects.get(id=trip_id, user=user)
        except Trip.DoesNotExist:
            raise serializers.ValidationError({"trip_id": "존재하지 않는 여행입니다."})

        print("🟢 creating wallet with →", validated_data)

        wallet, created = Wallet.objects.update_or_create(
            user=user,
            trip=trip,
            currency_unit=validated_data['currency_unit'],
            defaults={
                "country_code": validated_data["country_code"],
                "currency_code": validated_data["currency_code"],
                "quantity": validated_data["quantity"],
            }
        )
        return wallet

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'currency_unit', 'quantity']

class WalletUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['quantity']

class WalletDeductSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField()
    deductions = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'country', 'start_date', 'end_date', 'companions']
