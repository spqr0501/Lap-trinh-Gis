# URLS.PY - Định nghĩa URL routing cho app quanan
#
# View tĩnh: Render HTML với dữ liệu từ database
# API: Trả về JSON cho JavaScript

from django.urls import path
from . import views

urlpatterns = [
    # VIEW TĨNH - Render HTML
    path('', views.trang_chu, name='trang_chu'),
    path('danh-sach/', views.danh_sach_quan, name='danh_sach'),
    path('quan/<int:ma_quan>/', views.chi_tiet_quan, name='chi_tiet'),
    path('thong-ke/', views.thong_ke, name='thong_ke'),
    
    # API ENDPOINTS - Trả về JSON
    path('api/loai/', views.api_loai, name='api_loai'),
    path('api/quan/', views.api_quan, name='api_quan'),
    path('api/timkiem/', views.api_timkiem, name='api_timkiem'),
    path('api/goiy/<int:ma_quan>/', views.api_goiy, name='api_goiy'),
]
