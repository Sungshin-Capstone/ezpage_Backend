# models.py

from django.db import models
from django.conf import settings
from decimal import Decimal, InvalidOperation
from .services import ExchangeRateService

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
    currency = models.CharField(max_length=10, verbose_name="통화")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER', verbose_name="카테고리")
    description = models.TextField(blank=True, null=True, verbose_name="지출 설명")
    manual_input = models.BooleanField(default=False, verbose_name="수동 입력 여부")
    date = models.DateField(auto_now_add=True, verbose_name="지출 날짜")
    time = models.TimeField(auto_now_add=True, verbose_name="지출 시간")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} on {self.date}"

class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    trip = models.ForeignKey('Trip', on_delete=models.CASCADE, related_name='wallets')
    country_code = models.CharField(max_length=5)
    currency_code = models.CharField(max_length=5)
    currency_unit = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    converted_total_krw = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_balance(self, currency_unit, delta_quantity):
        if self.currency_unit != currency_unit:
            raise ValueError("통화 단위가 일치하지 않습니다.")
        if self.quantity + delta_quantity < 0:
            raise ValueError(f"{currency_unit} 단위 화폐가 부족합니다.")
        self.quantity += delta_quantity
        self.calculate_total_amount()
        self.save()

    def add_quantity(self, quantity):
        """
        같은 여행, 같은 화폐 단위의 지갑이면 수량을 누적해서 더합니다.
        """
        self.quantity += quantity
        self.calculate_total_amount()
        self.save()

    def calculate_total_amount(self):
        """총액을 계산하고 저장합니다."""
        self.total_amount = Decimal(str(self.currency_unit)) * Decimal(str(self.quantity))

    def get_wallet_dict(self):
        # 이 지갑 객체의 권종과 수량을 딕셔너리로 반환
        return {
            'currency_unit': self.currency_unit,
            'quantity': self.quantity,
            'currency_code': self.currency_code,
            'total_amount': float(self.total_amount),
            'converted_total_krw': float(self.converted_total_krw)
        }

    class Meta:
        unique_together = ('user', 'trip', 'currency_unit')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.trip} - {self.currency_unit}{self.currency_code} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.calculate_total_amount()
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
    exchange_rate_to_krw = models.DecimalField(max_digits=15, decimal_places=4, default=1.0, verbose_name="KRW 환율")  # KRW 대비 환율

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
        
        # 환율 정보 가져오기
        exchange_rate_info = ExchangeRateService.get_exchange_rate(self.currency_code)
        self.exchange_rate_to_krw = exchange_rate_info['rate']
        
        super().save(*args, **kwargs)
