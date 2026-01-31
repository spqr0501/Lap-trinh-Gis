"""
==========================================================
MODELS.PY - Định nghĩa các model ánh xạ với bảng PostGIS
==========================================================

Các model này ánh xạ với bảng đã tồn tại trong database.
managed = False nghĩa là Django KHÔNG quản lý schema 
(không tạo/xóa/sửa bảng).
"""

from django.db import models


class LoaiQuan(models.Model):
    """
    Model ánh xạ với bảng loai_quan.
    
    Bảng loai_quan lưu các loại quán ăn:
    - Phở, Bún, Cơm, Lẩu, Gà, Cafe...
    
    Fields:
    - ma_loai: Primary key (tự động tăng)
    - ten_loai: Tên loại quán (unique)
    """
    ma_loai = models.AutoField(primary_key=True)
    ten_loai = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'loai_quan'  # Tên bảng trong database
        managed = False         # Django không quản lý schema
    
    def __str__(self):
        return self.ten_loai


class QuanAn(models.Model):
    """
    Model ánh xạ với bảng quan_an.
    
    Bảng quan_an lưu thông tin quán ăn:
    - Thông tin cơ bản: tên, mô tả, địa chỉ
    - Đánh giá: điểm, số lượt
    - Vị trí: geometry POINT (PostGIS)
    
    Fields:
    - ma_quan: Primary key
    - ten_quan: Tên quán
    - mo_ta: Mô tả chi tiết
    - ma_loai: FK đến loai_quan
    - muc_gia: 1-5 ($ đến $$$$$)
    - diem_danh_gia: 0-5 sao
    - so_luot_danh_gia: Số lượt đánh giá
    - dia_chi: Địa chỉ text
    - vi_tri: geometry POINT (không map trong model)
    
    Lưu ý: Trường vi_tri (geometry) không được định nghĩa
    trong model vì Django không hỗ trợ trực tiếp.
    Ta dùng raw SQL với ST_X, ST_Y để lấy tọa độ.
    """
    ma_quan = models.AutoField(primary_key=True)
    ten_quan = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True, null=True)
    
    # Foreign key đến bảng loai_quan
    ma_loai = models.ForeignKey(
        LoaiQuan, 
        on_delete=models.SET_NULL,  # Nếu xóa loại -> set null
        null=True, 
        db_column='ma_loai'         # Tên cột trong database
    )
    
    muc_gia = models.SmallIntegerField(default=2)
    diem_danh_gia = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        default=0
    )
    so_luot_danh_gia = models.IntegerField(default=0)
    dia_chi = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'quan_an'
        managed = False
    
    def __str__(self):
        return self.ten_quan
