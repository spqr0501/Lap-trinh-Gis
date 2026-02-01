# MODELS.PY - Định nghĩa các model ánh xạ với bảng PostGIS
#
# managed = False nghĩa là Django KHÔNG quản lý schema

from django.db import models


class LoaiQuan(models.Model):
    # Bảng loai_quan: Phở, Bún, Cơm, Lẩu, Gà, Cafe...
    ma_loai = models.AutoField(primary_key=True)
    ten_loai = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'loai_quan'
        managed = False
    
    def __str__(self):
        return self.ten_loai


class QuanAn(models.Model):
    # Bảng quan_an: Thông tin quán ăn
    # Trường vi_tri (geometry) dùng raw SQL với ST_X, ST_Y
    
    ma_quan = models.AutoField(primary_key=True)
    ten_quan = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True, null=True)
    ma_loai = models.ForeignKey(
        LoaiQuan, 
        on_delete=models.SET_NULL,
        null=True, 
        db_column='ma_loai'
    )
    muc_gia = models.SmallIntegerField(default=2)
    diem_danh_gia = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    so_luot_danh_gia = models.IntegerField(default=0)
    dia_chi = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'quan_an'
        managed = False
    
    def __str__(self):
        return self.ten_quan
