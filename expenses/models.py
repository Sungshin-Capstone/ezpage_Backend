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
    created_at = models.DateTimeField(auto_now_add=True)

    def update_balance(self, currency_unit, delta_quantity):
        if self.currency_unit != currency_unit:
            raise ValueError("통화 단위가 일치하지 않습니다.")
        if self.quantity + delta_quantity < 0:
            raise ValueError(f"{currency_unit} 단위 화폐가 부족합니다.")
        self.quantity += delta_quantity
        self.save()

    def add_quantity(self, quantity):
        """
        같은 여행, 같은 화폐 단위의 지갑이면 수량을 누적해서 더합니다.
        """
        self.quantity += quantity
        self.save()

    def get_wallet_dict(self):
        # 이 지갑 객체의 권종과 수량을 딕셔너리로 반환
        return {self.currency_unit: self.quantity}

    class Meta:
        unique_together = ('user', 'trip', 'currency_unit')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.trip} - {self.currency_unit}{self.currency_code} x {self.quantity}"

    def _calculate_wallet_total(self, wallet):
        try:
            denomination = wallet.currency_unit
            quantity = wallet.quantity
            if denomination is None or quantity is None:
                return Decimal('0')
            return Decimal(str(denomination)) * Decimal(str(quantity))
        except (decimal.InvalidOperation, ValueError) as e:
            print(f"🔴 Decimal conversion error: denomination={denomination}, quantity={quantity}, error={e}")
            return Decimal('0')


class Trip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    name = models.CharField(max_length=100, verbose_name="여행 이름")
    country = models.CharField(max_length=5, verbose_name="나라")  # 예: 'JP', 'US', 'KR'
    start_date = models.DateField(verbose_name="시작일")
    end_date = models.DateField(verbose_name="종료일")
    color = models.CharField(max_length=7, default="#000000", verbose_name="색상")  # Hex color code
    companions = models.PositiveIntegerField(default=1, verbose_name="동행자 수")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s trip to {self.country} ({self.start_date} ~ {self.end_date})"
