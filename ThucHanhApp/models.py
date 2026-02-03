from django.db import models
from django.contrib.gis.db import models

# Create your models here.
class LoaiCuaHang(models.Model):
    ten_loai = models.CharField(max_length=100)
    mo_ta = models.TextField(blank=True)

    def __str__(self):
        return self.ten_loai


class CuaHang(models.Model):
    ten_cua_hang = models.CharField(max_length=200)
    dia_chi = models.TextField()
    loai = models.ForeignKey(LoaiCuaHang, on_delete=models.CASCADE)
    geom = models.PointField(srid=4326)

    def __str__(self):
        return self.ten_cua_hang