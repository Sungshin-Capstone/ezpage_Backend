# models.py

from django.db import models
from django.conf import settings

class Expense(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    is_scan_result = models.BooleanField(default=False, verbose_name="스캔 결과 여부")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="지출 금액")
    currency = models.CharField(max_length=10, verbose_name="통화")
    description = models.TextField(blank=True, null=True, verbose_name="지출 설명")
    manual_input = models.BooleanField(default=False, verbose_name="수동 입력 여부")
    date = models.DateField(auto_now_add=True, verbose_name="지출 날짜")
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

    def update_balance(self):
        pass  # 나중에 잔액 자동 계산용으로 사용 가능

    class Meta:
        unique_together = ('user', 'trip', 'currency_unit')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.trip} - {self.currency_unit}{self.currency_code} x {self.quantity}"


class Trip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    country = models.CharField(max_length=5)  # 예: 'JP', 'US', 'KR'
    start_date = models.DateField()
    end_date = models.DateField()
    companions = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s trip to {self.country} ({self.start_date} ~ {self.end_date})"
