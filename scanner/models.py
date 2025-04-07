# Create your models here.
from django.db import models

def scan_image_path(instance, filename):
    return f'scans/user_{instance.user.id}/{filename}'

def upload_scan_path(instance, filename):
    return f'scans/{instance.scan_type}/{filename}'

class ScanResult(models.Model):
    SCAN_TYPE_CHOICES = [
        ('receipt', 'AI 결제 가이드'),
        ('currency', '글로벌 머니 스캐너'),
    ]

    scan_type = models.CharField(max_length=20, choices=SCAN_TYPE_CHOICES)
    image = models.ImageField(upload_to=upload_scan_path)
    extracted_text = models.TextField(blank=True, null=True)
    extracted_data = models.JSONField(blank=True, null=True)  # 예: 메뉴명, 가격 등
    converted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    converted_currency = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


