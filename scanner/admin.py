# Register your models here.
# scanner/admin.py

from django.contrib import admin
from .models import ScanResult

@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'scan_type', 'converted_amount', 'converted_currency', 'created_at')
    search_fields = ('scan_type',)
    list_filter = ('scan_type', 'created_at')
