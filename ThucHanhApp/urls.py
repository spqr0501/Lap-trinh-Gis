from django.urls import path
from . import views

urlpatterns = [
    # Main page with all features integrated
    path('', views.trang_chu, name='trang_chu'),
    
    # GIS Tools API
    path('api/gis-tools/', views.api_gis_tools, name='api_gis_tools'),
    
    # Admin authentication
    path('quan-ly/login/', views.admin_login, name='admin_login'),
    path('quan-ly/logout/', views.admin_logout, name='admin_logout'),
    path('quan-ly/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin CRUD: Loai Cua Hang
    path('quan-ly/loai/', views.admin_loai_list, name='admin_loai_list'),
    path('quan-ly/loai/create/', views.admin_loai_create, name='admin_loai_create'),
    path('quan-ly/loai/<int:id>/update/', views.admin_loai_update, name='admin_loai_update'),
    path('quan-ly/loai/<int:id>/delete/', views.admin_loai_delete, name='admin_loai_delete'),
    
    # Admin CRUD: Cua Hang
    path('quan-ly/cuahang/', views.admin_cuahang_list, name='admin_cuahang_list'),
    path('quan-ly/cuahang/create/', views.admin_cuahang_create, name='admin_cuahang_create'),
    path('quan-ly/cuahang/<int:id>/update/', views.admin_cuahang_update, name='admin_cuahang_update'),
    path('quan-ly/cuahang/<int:id>/delete/', views.admin_cuahang_delete, name='admin_cuahang_delete'),
    
    # Admin CRUD: Danh Gia
    path('quan-ly/danhgia/', views.admin_danhgia_list, name='admin_danhgia_list'),
    path('quan-ly/danhgia/create/', views.admin_danhgia_create, name='admin_danhgia_create'),
    path('quan-ly/danhgia/<int:id>/update/', views.admin_danhgia_update, name='admin_danhgia_update'),
    path('quan-ly/danhgia/<int:id>/delete/', views.admin_danhgia_delete, name='admin_danhgia_delete'),
    
    # Admin CRUD: Su Kien
    path('quan-ly/sukien/', views.admin_sukien_list, name='admin_sukien_list'),
    path('quan-ly/sukien/create/', views.admin_sukien_create, name='admin_sukien_create'),
    path('quan-ly/sukien/<int:id>/update/', views.admin_sukien_update, name='admin_sukien_update'),
    path('quan-ly/sukien/<int:id>/delete/', views.admin_sukien_delete, name='admin_sukien_delete'),
    
    # Admin CRUD: Cua Hang - Su Kien
    path('quan-ly/cuahang-sukien/', views.admin_cuahang_sukien_list, name='admin_cuahang_sukien_list'),
    path('quan-ly/cuahang-sukien/create/', views.admin_cuahang_sukien_create, name='admin_cuahang_sukien_create'),
    path('quan-ly/cuahang-sukien/<int:id>/delete/', views.admin_cuahang_sukien_delete, name='admin_cuahang_sukien_delete'),
]
