from django.urls import path
from . import views

urlpatterns = [
    # Main page with all features integrated
    path('', views.trang_chu, name='trang_chu'),
    
    # GIS Tools API
    path('api/gis-tools/', views.api_gis_tools, name='api_gis_tools'),
    path('api/danh-gia/<int:cua_hang_id>/', views.api_danh_gia, name='api_danh_gia'),
    path('api/gui-danh-gia/<int:cua_hang_id>/', views.api_gui_danh_gia, name='api_gui_danh_gia'),
    path('api/like-danh-gia/<int:danh_gia_id>/', views.api_like_danh_gia, name='api_like_danh_gia'),
    path('api/admin-thong-bao/', views.api_admin_thong_bao, name='api_admin_thong_bao'),
    path('api/admin-thong-bao/<int:id>/doc/', views.api_admin_thong_bao_doc, name='api_admin_thong_bao_doc'),
    path('api/admin-thong-bao/doc-tat-ca/', views.api_admin_thong_bao_doc_tat_ca, name='api_admin_thong_bao_doc_tat_ca'),
    
    # Admin authentication
    path('quan-ly/login/', views.admin_login, name='admin_login'),
    path('quan-ly/logout/', views.admin_logout, name='admin_logout'),
    path('quan-ly/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/dashboard-revenue/', views.api_dashboard_revenue, name='api_dashboard_revenue'),
    path('quan-ly/audit-log/', views.admin_audit_log, name='admin_audit_log'),
    path('quan-ly/thong-bao/', views.admin_thong_bao_list, name='admin_thong_bao_list'),
    path('quan-ly/thong-bao/<int:id>/doc/', views.admin_thong_bao_doc, name='admin_thong_bao_doc'),
    path('quan-ly/thong-bao/doc-tat-ca/', views.admin_thong_bao_doc_tat_ca, name='admin_thong_bao_doc_tat_ca'),
    path('quan-ly/thong-bao/xoa-da-doc/', views.admin_thong_bao_xoa_da_doc, name='admin_thong_bao_xoa_da_doc'),
    path('quan-ly/thong-bao/<int:id>/xoa/', views.admin_thong_bao_xoa, name='admin_thong_bao_xoa'),
    
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
    path('quan-ly/cuahang-sukien/<int:id>/update/', views.admin_cuahang_sukien_update, name='admin_cuahang_sukien_update'),
    path('quan-ly/cuahang-sukien/<int:id>/delete/', views.admin_cuahang_sukien_delete, name='admin_cuahang_sukien_delete'),

    # Admin CRUD: Mat Hang
    path('quan-ly/mathang/', views.admin_mathang_list, name='admin_mathang_list'),
    path('quan-ly/mathang/create/', views.admin_mathang_create, name='admin_mathang_create'),
    path('quan-ly/mathang/<int:id>/update/', views.admin_mathang_update, name='admin_mathang_update'),
    path('quan-ly/mathang/<int:id>/delete/', views.admin_mathang_delete, name='admin_mathang_delete'),

    # Admin CRUD: Ton Kho
    path('quan-ly/tonkho/', views.admin_tonkho_list, name='admin_tonkho_list'),
    path('quan-ly/tonkho/create/', views.admin_tonkho_create, name='admin_tonkho_create'),
    path('quan-ly/tonkho/<int:id>/update/', views.admin_tonkho_update, name='admin_tonkho_update'),
    path('quan-ly/tonkho/<int:id>/delete/', views.admin_tonkho_delete, name='admin_tonkho_delete'),
    path('quan-ly/tonkho/import-excel/', views.admin_tonkho_import_excel, name='admin_tonkho_import_excel'),

    # Admin CRUD: Don Hang
    path('quan-ly/donhang/', views.admin_donhang_list, name='admin_donhang_list'),
    path('quan-ly/donhang/export-csv/', views.admin_donhang_export_csv, name='admin_donhang_export_csv'),
    path('quan-ly/donhang/create/', views.admin_donhang_create, name='admin_donhang_create'),
    path('quan-ly/donhang/<int:id>/', views.admin_donhang_detail, name='admin_donhang_detail'),
    path('quan-ly/donhang/<int:id>/update/', views.admin_donhang_update, name='admin_donhang_update'),
    path('quan-ly/donhang/<int:id>/delete/', views.admin_donhang_delete, name='admin_donhang_delete'),

    # Doanh Thu
    path('quan-ly/doanhthu/', views.admin_doanhthu, name='admin_doanhthu'),
    path('quan-ly/doanhthu/export-excel/', views.admin_doanhthu_export_excel, name='admin_doanhthu_export_excel'),
    path('quan-ly/doanhthu/export-pdf/', views.admin_doanhthu_export_pdf, name='admin_doanhthu_export_pdf'),
    path('quan-ly/doanhthu/chitiet/', views.admin_doanhthu_chitiet, name='admin_doanhthu_chitiet'),

    # User: Dang ky, Dang nhap
    path('dang-ky/', views.user_register, name='user_register'),
    path('dang-nhap/', views.user_login, name='user_login'),
    path('dang-xuat/', views.user_logout, name='user_logout'),
    path('ho-so/', views.user_profile, name='user_profile'),

    # User: Dat hang
    path('dat-hang/<int:cua_hang_id>/', views.user_dat_hang, name='user_dat_hang'),
    path('don-hang-cua-toi/', views.user_don_hang, name='user_don_hang'),
    path('api/don-hang/<int:id>/', views.api_user_donhang_detail, name='api_user_donhang_detail'),

    # User: Gio Hang
    path('gio-hang/', views.user_giohang, name='user_giohang'),
    path('gio-hang/thanh-toan-tat-ca/', views.user_giohang_thanhtoan_all, name='user_giohang_thanhtoan_all'),
    path('gio-hang/thanh-toan/<int:cua_hang_id>/', views.user_giohang_thanhtoan, name='user_giohang_thanhtoan'),
    path('api/gio-hang/add/', views.api_giohang_add, name='api_giohang_add'),
    path('gio-hang/xoa/<int:id>/', views.user_giohang_xoa, name='user_giohang_xoa'),

    # Stripe Payment
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),
]
