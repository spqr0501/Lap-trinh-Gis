"""
Admin đơn giản
"""
from django.contrib import admin
from .models import LoaiQuan, QuanAn


@admin.register(LoaiQuan)
class LoaiQuanAdmin(admin.ModelAdmin):
    list_display = ['ma_loai', 'ten_loai']


@admin.register(QuanAn)
class QuanAnAdmin(admin.ModelAdmin):
    list_display = ['ma_quan', 'ten_quan', 'ma_loai', 'muc_gia', 'diem_danh_gia']
    list_filter = ['ma_loai', 'muc_gia']
    search_fields = ['ten_quan']
