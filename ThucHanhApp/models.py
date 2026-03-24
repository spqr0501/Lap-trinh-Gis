from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


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
    nguoi_dung = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='danh_gias')
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


class DanhGiaLike(models.Model):
    danh_gia = models.ForeignKey(DanhGia, on_delete=models.CASCADE, related_name='likes')
    nguoi_dung = models.ForeignKey(User, on_delete=models.CASCADE, related_name='danh_gia_likes')
    thoi_gian = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'danh_gia_like'
        verbose_name = 'Like đánh giá'
        verbose_name_plural = 'Like đánh giá'
        unique_together = ('danh_gia', 'nguoi_dung')
        ordering = ['-thoi_gian']

    def __str__(self):
        return f"{self.nguoi_dung.username} like DG#{self.danh_gia_id}"


class DanhGiaAnh(models.Model):
    danh_gia = models.ForeignKey(DanhGia, on_delete=models.CASCADE, related_name='hinh_anhs')
    hinh_anh = models.ImageField(upload_to='danh_gia/')
    thoi_gian_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'danh_gia_anh'
        verbose_name = 'Ảnh đánh giá'
        verbose_name_plural = 'Ảnh đánh giá'
        ordering = ['thoi_gian_tao']

    def __str__(self):
        return f"Ảnh đánh giá #{self.id} - DG#{self.danh_gia_id}"


class SuKien(models.Model):
    NGAY_TRONG_TUAN = [
        (0, 'Thứ Hai'),
        (1, 'Thứ Ba'),
        (2, 'Thứ Tư'),
        (3, 'Thứ Năm'),
        (4, 'Thứ Sáu'),
        (5, 'Thứ Bảy'),
        (6, 'Chủ Nhật'),
    ]

    ten_su_kien = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True)
    ngay_bat_dau = models.DateField()
    ngay_ket_thuc = models.DateField()
    la_hang_tuan = models.BooleanField(default=False, verbose_name='Sự kiện hàng tuần')
    ngay_trong_tuan = models.CharField(
        max_length=20, blank=True, default='',
        verbose_name='Ngày trong tuần'
    )

    class Meta:
        db_table = 'su_kien'
        verbose_name = 'Sự kiện'
        verbose_name_plural = 'Sự kiện'
        ordering = ['-ngay_bat_dau']

    @property
    def dang_dien_ra(self):
        from datetime import date
        today = date.today()
        if self.la_hang_tuan:
            return today.weekday() in self.get_ngay_trong_tuan_list()
        else:
            if not self.ngay_bat_dau or not self.ngay_ket_thuc:
                return False
            return self.ngay_bat_dau <= today <= self.ngay_ket_thuc

    def get_ngay_trong_tuan_list(self):
        """Tra ve danh sach cac ngay trong tuan da chon (list of int)"""
        if not self.ngay_trong_tuan:
            return []
        return [int(x) for x in self.ngay_trong_tuan.split(',') if x.strip().isdigit()]

    def get_ngay_trong_tuan_display_list(self):
        """Tra ve ten cac ngay da chon"""
        mapping = dict(self.NGAY_TRONG_TUAN)
        return [mapping.get(d, '') for d in self.get_ngay_trong_tuan_list()]

    def __str__(self):
        if self.la_hang_tuan and self.ngay_trong_tuan:
            ten_ngays = ', '.join(self.get_ngay_trong_tuan_display_list())
            return f"{self.ten_su_kien} (Hàng tuần - {ten_ngays})"
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


# ====== QUAN LY KHO ======

class MatHang(models.Model):
    ten_mat_hang = models.CharField(max_length=200)
    don_vi = models.CharField(max_length=50, default='cái')
    gia_ban = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    mo_ta = models.TextField(blank=True)

    class Meta:
        db_table = 'mat_hang'
        verbose_name = 'Mặt hàng'
        verbose_name_plural = 'Mặt hàng'
        ordering = ['ten_mat_hang']

    def __str__(self):
        return self.ten_mat_hang


class TonKho(models.Model):
    cua_hang = models.ForeignKey(CuaHang, on_delete=models.CASCADE, related_name='ton_khos')
    mat_hang = models.ForeignKey(MatHang, on_delete=models.CASCADE, related_name='ton_khos')
    so_luong = models.IntegerField(default=0)

    class Meta:
        db_table = 'ton_kho'
        verbose_name = 'Tồn kho'
        verbose_name_plural = 'Tồn kho'
        unique_together = ('cua_hang', 'mat_hang')

    def __str__(self):
        return f"{self.cua_hang.ten_cua_hang} - {self.mat_hang.ten_mat_hang}: {self.so_luong}"


# ====== QUAN LY DON HANG ======

class DonHang(models.Model):
    TRANG_THAI_CHOICES = [
        ('cho_xu_ly', 'Chờ xử lý'),
        ('dang_giao', 'Đang giao'),
        ('da_thanh_toan', 'Đã thanh toán'),
        ('da_huy', 'Đã hủy'),
    ]

    cua_hang = models.ForeignKey(CuaHang, on_delete=models.CASCADE, related_name='don_hangs')
    nguoi_dung = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='don_hangs')
    ngay_dat = models.DateTimeField(auto_now_add=True)
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_CHOICES, default='cho_xu_ly')
    tong_tien = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    ghi_chu = models.TextField(blank=True)

    class Meta:
        db_table = 'don_hang'
        verbose_name = 'Đơn hàng'
        verbose_name_plural = 'Đơn hàng'
        ordering = ['-ngay_dat']

    def cap_nhat_tong_tien(self):
        tong = sum(ct.thanh_tien for ct in self.chi_tiets.all())
        self.tong_tien = tong
        self.save()

    def __str__(self):
        return f"DH-{self.id} ({self.cua_hang.ten_cua_hang}) - {self.get_trang_thai_display()}"


class ChiTietDonHang(models.Model):
    don_hang = models.ForeignKey(DonHang, on_delete=models.CASCADE, related_name='chi_tiets')
    mat_hang = models.ForeignKey(MatHang, on_delete=models.CASCADE)
    so_luong = models.IntegerField(default=1)
    don_gia = models.DecimalField(max_digits=12, decimal_places=0)
    thanh_tien = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    class Meta:
        db_table = 'chi_tiet_don_hang'
        verbose_name = 'Chi tiết đơn hàng'
        verbose_name_plural = 'Chi tiết đơn hàng'

    def save(self, *args, **kwargs):
        self.thanh_tien = self.so_luong * self.don_gia
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.mat_hang.ten_mat_hang} x{self.so_luong}"


class AuditLog(models.Model):
    HANH_DONG_CHOICES = [
        ('create', 'Tạo mới'),
        ('update', 'Cập nhật'),
        ('delete', 'Xóa'),
        ('view', 'Xem'),
        ('export', 'Xuất dữ liệu'),
        ('other', 'Khác'),
    ]

    nguoi_dung = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    module = models.CharField(max_length=100)
    hanh_dong = models.CharField(max_length=20, choices=HANH_DONG_CHOICES, default='other')
    mo_ta = models.TextField()
    ip_address = models.CharField(max_length=50, blank=True, default='')
    thoi_gian = models.DateTimeField(auto_now_add=True)
    doi_tuong = models.CharField(max_length=100, blank=True, default='')
    doi_tuong_id = models.IntegerField(null=True, blank=True)
    du_lieu_truoc = models.JSONField(null=True, blank=True)
    du_lieu_sau = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Nhật ký thao tác'
        verbose_name_plural = 'Nhật ký thao tác'
        ordering = ['-thoi_gian']

    def __str__(self):
        return f"[{self.module}] {self.get_hanh_dong_display()} - {self.thoi_gian:%d/%m/%Y %H:%M}"


class AdminThongBao(models.Model):
    nguoi_dung = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_thong_baos')
    don_hang = models.ForeignKey(DonHang, on_delete=models.CASCADE, null=True, blank=True, related_name='admin_thong_baos')
    tieu_de = models.CharField(max_length=255)
    noi_dung = models.TextField(blank=True, default='')
    da_doc = models.BooleanField(default=False)
    thoi_gian_tao = models.DateTimeField(auto_now_add=True)
    thoi_gian_doc = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'admin_thong_bao'
        verbose_name = 'Thông báo admin'
        verbose_name_plural = 'Thông báo admin'
        ordering = ['-thoi_gian_tao']

    def __str__(self):
        return f"TB#{self.id} - {self.tieu_de}"