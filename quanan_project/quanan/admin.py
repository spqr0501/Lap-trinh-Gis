"""
==========================================================
ADMIN.PY - Cấu hình Django Admin cho quản lý quán ăn
==========================================================

Đăng ký các model để quản lý qua giao diện /admin/
"""

from django.contrib import admin
from .models import LoaiQuan, QuanAn


@admin.register(LoaiQuan)
class LoaiQuanAdmin(admin.ModelAdmin):
    """
    Admin config cho model LoaiQuan.
    
    list_display: Các cột hiển thị trong danh sách
    """
    list_display = ['ma_loai', 'ten_loai']


@admin.register(QuanAn)
class QuanAnAdmin(admin.ModelAdmin):
    """
    Admin config cho model QuanAn.
    
    list_display: Các cột hiển thị trong danh sách
    list_filter: Bộ lọc bên phải
    search_fields: Tìm kiếm theo field
    """
    list_display = ['ma_quan', 'ten_quan', 'ma_loai', 'muc_gia', 'diem_danh_gia']
    list_filter = ['ma_loai', 'muc_gia']  # Lọc theo loại và mức giá
    search_fields = ['ten_quan']           # Tìm theo tên quán
