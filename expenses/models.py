# Create your models here.
from django.db import models
from django.conf import settings

def receipt_image_path(instance, filename):
    return f'expenses/user_{instance.user.username}/{filename}'

class Expense(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="지출 금액")
    currency = models.CharField(max_length=10, verbose_name="통화")
    description = models.TextField(blank=True, null=True, verbose_name="지출 설명")
    image = models.ImageField(upload_to=receipt_image_path, blank=True, null=True, verbose_name="가격표 이미지")
    manual_input = models.BooleanField(default=False, verbose_name="수동 입력 여부")
    date = models.DateField(auto_now_add=True, verbose_name="지출 날짜")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} on {self.date}"
