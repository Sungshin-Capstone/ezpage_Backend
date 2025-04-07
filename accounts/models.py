# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

def user_profile_path(instance, filename):
    return f'profiles/user_{instance.username}/{filename}'

class User(AbstractUser):
    profile_image = models.ImageField(upload_to=user_profile_path, blank=True, null=True, verbose_name="프로필 이미지")
    name = models.CharField(max_length=100, verbose_name="이름")
    nickname = models.CharField(max_length=100, verbose_name="닉네임")
    username = models.CharField(max_length=150, unique=True, verbose_name="아이디")
    email = models.EmailField(unique=True, verbose_name="email")
    country = models.CharField(max_length=50, verbose_name="국가")

    REQUIRED_FIELDS = ['email', 'name', 'nickname', 'country']
    USERNAME_FIELD = 'username'

    def __str__(self):
        return f'{self.username} ({self.nickname})'
