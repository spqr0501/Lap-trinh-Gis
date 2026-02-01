# VIEWS.PY - Xử lý API và View tĩnh với GeoDjango ORM

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from .models import LoaiQuan, QuanAn


# ============================================================
# VIEW TĨNH - Render dữ liệu trực tiếp vào HTML
# ============================================================

def trang_chu(request):
    # Trang chủ - Bản đồ (dùng JavaScript load dữ liệu)
    return render(request, 'quanan/bando.html')


def trang_timkiem(request):
    # Trang tìm kiếm riêng
    return render(request, 'quanan/timkiem.html')


def danh_sach_quan(request):
    # VIEW TĨNH: Hiển thị danh sách quán (không cần JavaScript)
    loai_filter = request.GET.get('loai', None)
    
    quans = QuanAn.objects.select_related('ma_loai').all().order_by('-diem_danh_gia')
    
    if loai_filter:
        quans = quans.filter(ma_loai__ten_loai=loai_filter)
    
    loais = LoaiQuan.objects.all()
    
    context = {
        'quans': quans,
        'loais': loais,
        'loai_hien_tai': loai_filter,
        'tong_quan': quans.count(),
    }
    return render(request, 'quanan/danh_sach.html', context)


def chi_tiet_quan(request, ma_quan):
    # VIEW TĨNH: Chi tiết 1 quán ăn
    quan = get_object_or_404(QuanAn, ma_quan=ma_quan)
    
    # Lấy quán cùng loại
    quans_tuong_tu = QuanAn.objects.select_related('ma_loai').filter(
        ma_loai=quan.ma_loai
    ).exclude(ma_quan=ma_quan).order_by('-diem_danh_gia')[:5]
    
    context = {
        'quan': quan,
        'quans_tuong_tu': quans_tuong_tu,
    }
    return render(request, 'quanan/chi_tiet.html', context)


def thong_ke(request):
    # VIEW TĨNH: Thống kê tổng quan
    from django.db.models import Count, Avg
    
    tong_quan = QuanAn.objects.count()
    tong_loai = LoaiQuan.objects.count()
    diem_tb = QuanAn.objects.aggregate(Avg('diem_danh_gia'))['diem_danh_gia__avg']
    
    # Thống kê theo loại
    thong_ke_loai = QuanAn.objects.values('ma_loai__ten_loai').annotate(
        so_luong=Count('ma_quan'),
        diem_tb=Avg('diem_danh_gia')
    ).order_by('-so_luong')
    
    context = {
        'tong_quan': tong_quan,
        'tong_loai': tong_loai,
        'diem_tb': round(diem_tb or 0, 1),
        'thong_ke_loai': thong_ke_loai,
    }
    return render(request, 'quanan/thong_ke.html', context)


# ============================================================
# API ENDPOINTS - Trả về JSON cho JavaScript
# ============================================================

def api_loai(request):
    # API: Lấy danh sách loại quán ăn
    data = list(LoaiQuan.objects.values('ma_loai', 'ten_loai'))
    return JsonResponse({'status': 'success', 'data': data})


def api_quan(request):
    # API: Lấy danh sách tất cả quán ăn
    quans = QuanAn.objects.select_related('ma_loai').all().order_by('-diem_danh_gia')
    
    data = [{
        'ma_quan': q.ma_quan,
        'ten_quan': q.ten_quan,
        'loai': q.ma_loai.ten_loai if q.ma_loai else None,
        'muc_gia': q.muc_gia,
        'diem': float(q.diem_danh_gia or 0),
        'so_luot': q.so_luot_danh_gia,
        'dia_chi': q.dia_chi,
        'kinh_do': q.kinh_do,
        'vi_do': q.vi_do,
    } for q in quans]
    
    return JsonResponse({'status': 'success', 'data': data})


def api_timkiem(request):
    # API: Tìm quán ăn trong bán kính
    lat = float(request.GET.get('lat', 10.78))
    lng = float(request.GET.get('lng', 106.70))
    r = float(request.GET.get('r', 2))
    
    diem_tim = Point(lng, lat, srid=4326)
    
    quans = QuanAn.objects.select_related('ma_loai').filter(
        vi_tri__distance_lte=(diem_tim, D(km=r))
    ).annotate(
        khoang_cach=Distance('vi_tri', diem_tim)
    ).order_by('khoang_cach')
    
    data = [{
        'ma_quan': q.ma_quan,
        'ten_quan': q.ten_quan,
        'loai': q.ma_loai.ten_loai if q.ma_loai else None,
        'muc_gia': q.muc_gia,
        'diem': float(q.diem_danh_gia or 0),
        'kinh_do': q.kinh_do,
        'vi_do': q.vi_do,
        'khoang_cach': round(q.khoang_cach.km, 2),
    } for q in quans]
    
    return JsonResponse({'status': 'success', 'data': data})


def api_goiy(request, ma_quan):
    # API: Gợi ý quán CÙNG LOẠI
    top = int(request.GET.get('top', 5))
    
    try:
        quan_hientai = QuanAn.objects.get(ma_quan=ma_quan)
    except QuanAn.DoesNotExist:
        return JsonResponse({'status': 'error', 'data': []})
    
    if not quan_hientai.ma_loai:
        return JsonResponse({'status': 'error', 'data': []})
    
    quans = QuanAn.objects.select_related('ma_loai').filter(
        ma_loai=quan_hientai.ma_loai
    ).exclude(ma_quan=ma_quan).order_by('-diem_danh_gia')[:top]
    
    data = [{
        'ma_quan': q.ma_quan,
        'ten_quan': q.ten_quan,
        'loai': q.ma_loai.ten_loai if q.ma_loai else None,
        'muc_gia': q.muc_gia,
        'diem': float(q.diem_danh_gia or 0),
        'kinh_do': q.kinh_do,
        'vi_do': q.vi_do,
    } for q in quans]
    
    return JsonResponse({'status': 'success', 'data': data})
