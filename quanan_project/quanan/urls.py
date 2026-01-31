"""
==========================================================
URLS.PY - Định nghĩa URL routing cho app quanan
==========================================================

Ánh xạ URL -> View function:
- /           -> Trang bản đồ
- /api/loai/  -> API danh sách loại
- /api/quan/  -> API danh sách quán
- /api/timkiem/ -> API tìm theo vị trí
- /api/goiy/  -> API gợi ý quán tương tự
"""

from django.urls import path
from . import views

urlpatterns = [
    # Trang chính - Bản đồ
    path('', views.trang_chu),
    
    # API endpoints
    path('api/loai/', views.api_loai),           # Danh sách loại quán
    path('api/quan/', views.api_quan),           # Tất cả quán ăn
    path('api/timkiem/', views.api_timkiem),     # Tìm theo vị trí + bán kính
    path('api/goiy/<int:ma_quan>/', views.api_goiy),  # Gợi ý tương tự
]
