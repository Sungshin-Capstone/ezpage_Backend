from rest_framework import serializers
from .models import ScanResult

class ScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanResult
        fields = '__all__'

class ReceiptScanSerializer(serializers.Serializer):
    image = serializers.ImageField()
