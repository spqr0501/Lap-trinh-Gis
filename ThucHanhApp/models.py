from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.
class LoaiCuaHang(models.Model):
    ten_loai = models.CharField(max_length=100)
    mo_ta = models.TextField(blank=True)

    class Meta:
        db_table = 'loai_cua_hang'
        verbose_name = 'Loại cửa hàng'
        verbose_name_plural = 'Loại cửa hàng'

    def __str__(self):
        return self.ten_loai


class CuaHang(models.Model):
    ten_cua_hang = models.CharField(max_length=200)
    dia_chi = models.TextField()
    loai = models.ForeignKey(LoaiCuaHang, on_delete=models.CASCADE, related_name='cua_hangs')
    geom = models.PointField(srid=4326)

    class Meta:
        db_table = 'cua_hang'
        verbose_name = 'Cửa hàng'
        verbose_name_plural = 'Cửa hàng'

    def __str__(self):
        return self.ten_cua_hang


class DanhGia(models.Model):
    cua_hang = models.ForeignKey(CuaHang, on_delete=models.CASCADE, related_name='danh_gias')
    diem = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    nhan_xet = models.TextField(blank=True)
    ngay_danh_gia = models.DateField()

    class Meta:
        db_table = 'danh_gia'
        verbose_name = 'Đánh giá'
        verbose_name_plural = 'Đánh giá'
        ordering = ['-ngay_danh_gia']

    def __str__(self):
        return f"{self.cua_hang.ten_cua_hang} - {self.diem} sao"


class SuKien(models.Model):
    ten_su_kien = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True)
    ngay_bat_dau = models.DateField()
    ngay_ket_thuc = models.DateField()

    class Meta:
        db_table = 'su_kien'
        verbose_name = 'Sự kiện'
        verbose_name_plural = 'Sự kiện'
        ordering = ['-ngay_bat_dau']

    def __str__(self):
        return self.ten_su_kien


class CuaHangSuKien(models.Model):
    cua_hang = models.ForeignKey(CuaHang, on_delete=models.CASCADE, related_name='su_kiens')
    su_kien = models.ForeignKey(SuKien, on_delete=models.CASCADE, related_name='cua_hangs')

    class Meta:
        db_table = 'cua_hang_su_kien'
        verbose_name = 'Cửa hàng - Sự kiện'
        verbose_name_plural = 'Cửa hàng - Sự kiện'
        unique_together = ('cua_hang', 'su_kien')

    def __str__(self):
        return f"{self.cua_hang.ten_cua_hang} - {self.su_kien.ten_su_kien}"