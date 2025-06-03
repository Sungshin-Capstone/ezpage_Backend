from django.db import models
from django.conf import settings
from decimal import Decimal

class ScanResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='scan_images/', blank=True, null=True) # 이미지 필드는 필요에 따라 수정
    scan_type = models.CharField(max_length=20, blank=True, null=True)
    extracted_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    converted_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    converted_currency = models.CharField(max_length=10, blank=True, null=True)
    extracted_data = models.JSONField(blank=True, null=True)
    
    # Add fields for wallet total and exchange rate
    wallet_total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)

    class Meta:
        db_table = 'scanner_scanresult'

    def __str__(self):
        return f"Scan Result {self.id} for {self.user.username}" 