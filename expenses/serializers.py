# serializers.py

from rest_framework import serializers
from .models import Expense,Wallet,Trip

class ScanResultExpenseSerializer(serializers.ModelSerializer):
    currency = serializers.ChoiceField(choices=["KRW", "JPY", "CNY", "USD"])

    class Meta:
        model = Expense
        fields = ['id', 'amount', 'currency', 'description']

class ExpenseSerializer(serializers.ModelSerializer):
    currency = serializers.ChoiceField(choices=["KRW", "JPY", "CNY", "USD"])
    category = serializers.ChoiceField(choices=Expense.CATEGORY_CHOICES)
    is_scan_result = serializers.BooleanField(required=False, default=False)
    time = serializers.SerializerMethodField()
    amount = serializers.IntegerField()

    class Meta:
        model = Expense
        fields = ['id', 'user', 'amount', 'currency', 'category', 'description', 'manual_input', 'date', 'time', 'created_at', 'is_scan_result']
        read_only_fields = ['id', 'user', 'created_at']

    def get_time(self, obj):
        if obj.time:
            return obj.time.strftime("%H:%M")
        return None

    def get_amount(self, obj):
        return int(obj.amount)


class WalletScanResultSerializer(serializers.ModelSerializer):
    trip_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Wallet
        fields = ['trip_id', 'country_code', 'currency_code', 'currency_unit', 'quantity']

    def create(self, validated_data):
        user = self.context['request'].user
        trip_id = validated_data.pop('trip_id')

        try:
            trip = Trip.objects.get(id=trip_id, user=user)
        except Trip.DoesNotExist:
            raise serializers.ValidationError({"trip_id": "존재하지 않는 여행입니다."})

        # validated_data를 수정하지 말고, defaults만 명시적으로 설정
        wallet, created = Wallet.objects.update_or_create(
            user=user,
            trip=trip,
            currency_unit=validated_data['currency_unit'],
            defaults={
                "country_code": validated_data["country_code"],
                "currency_code": validated_data["currency_code"],
                "quantity": validated_data["quantity"],
                # user와 trip은 조건절에 이미 있으므로 defaults에서 제외
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
        fields = ['id', 'name', 'country', 'start_date', 'end_date', 'color', 'companions']
        read_only_fields = ['id']
