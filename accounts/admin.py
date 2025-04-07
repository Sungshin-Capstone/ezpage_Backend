from django.contrib import admin

# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'name', 'nickname', 'country', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ("추가 정보", {"fields": ("name", "nickname", "country", "profile_image")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("추가 정보", {"fields": ("name", "nickname", "country", "profile_image")}),
    )
