# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # 사용자 정보
    name = models.CharField(max_length=30)  # 이름(실명)
    nickname = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    country = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.username