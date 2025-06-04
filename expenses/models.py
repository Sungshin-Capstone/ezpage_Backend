# models.py

from django.db import models
from django.conf import settings
from decimal import Decimal, InvalidOperation

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('FOOD', '식비'),
        ('TRANSPORT', '교통'),
        ('SHOPPING', '쇼핑'),
        ('ETC', '기타'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    is_scan_result = models.BooleanField(default=False, verbose_name="스캔 결과 여부")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="지출 금액")
    currency_code = models.CharField(max_length=10, verbose_name="통화 코드")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER', verbose_name="카테고리")
    description = models.TextField(blank=True, null=True, verbose_name="지출 설명")
    manual_input = models.BooleanField(default=False, verbose_name="수동 입력 여부")
    date = models.DateField(auto_now_add=True, verbose_name="지출 날짜")
    time = models.TimeField(auto_now_add=True, verbose_name="지출 시간")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency_code} on {self.date}"

class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    trip = models.ForeignKey('Trip', on_delete=models.CASCADE, related_name='wallets')
    country_code = models.CharField(max_length=5)
    currency_code = models.CharField(max_length=5)
    
    denominations = models.JSONField(default=dict)
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))  # 외화 총액
    converted_total_krw = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))  # 원화 환산 총액

    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_total_amount(self):
        total = Decimal('0')
        for key, qty in self.denominations.items():
            # 키에서 숫자만 추출 (예: "USD_50dollar" → 50)
            match = re.search(r'(\d+)', key)
            if match:
                unit = Decimal(match.group(1))
                total += unit * Decimal(qty)
        self.total_amount = total
        def save(self, *args, **kwargs):
            self.calculate_total_amount()  # total_amount 계산
            super().save(*args, **kwargs)


class Trip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=5, verbose_name="나라")  # 예: 'JP', 'US', 'KR'
    currency_code = models.CharField(max_length=5, default='KRW', verbose_name="기본 통화")  # 기본 통화 코드
    start_date = models.DateField()
    end_date = models.DateField()
    color = models.CharField(max_length=7, default="#000000", verbose_name="색상")  # Hex color code
    companions = models.PositiveIntegerField(default=1, verbose_name="동행자 수")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_wallet_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 국가 코드에 따른 기본 통화 설정
        currency_mapping = {
            'US': 'USD',
            'JP': 'JPY',
            'CN': 'CNY',
            'KR': 'KRW'
        }
        self.currency_code = currency_mapping.get(self.country, 'KRW')
        super().save(*args, **kwargs)
