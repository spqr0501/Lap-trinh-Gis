# MODELS.PY - Định nghĩa model với GeoDjango (hỗ trợ PostGIS)

from django.contrib.gis.db import models


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
    # Bảng quan_an: Thông tin quán ăn với vị trí địa lý
    
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
    
    # TRƯỜNG GEOMETRY - GeoDjango hỗ trợ PostGIS
    vi_tri = models.PointField(srid=4326, null=True, blank=True)
    
    class Meta:
        db_table = 'quan_an'
        managed = False
    
    def __str__(self):
        return self.ten_quan
    
    # Property để lấy tọa độ dễ dàng
    @property
    def kinh_do(self):
        return self.vi_tri.x if self.vi_tri else None
    
    @property
    def vi_do(self):
        return self.vi_tri.y if self.vi_tri else None
