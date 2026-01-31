"""
Views đơn giản - gộp tất cả API
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
import json


def trang_chu(request):
    """Trang bản đồ"""
    return render(request, 'quanan/bando.html')


def api_loai(request):
    """API: Danh sách loại quán"""
    with connection.cursor() as c:
        c.execute("SELECT ma_loai, ten_loai FROM loai_quan")
        data = [{'ma_loai': r[0], 'ten_loai': r[1]} for r in c.fetchall()]
    return JsonResponse({'status': 'success', 'data': data})


def api_quan(request):
    """API: Danh sách quán ăn với tọa độ"""
    sql = """
    SELECT q.ma_quan, q.ten_quan, l.ten_loai, q.muc_gia, 
           q.diem_danh_gia, q.so_luot_danh_gia, q.dia_chi,
           ST_X(q.vi_tri), ST_Y(q.vi_tri)
    FROM quan_an q LEFT JOIN loai_quan l ON q.ma_loai = l.ma_loai
    ORDER BY q.diem_danh_gia DESC
    """
    with connection.cursor() as c:
        c.execute(sql)
        data = [{
            'ma_quan': r[0], 'ten_quan': r[1], 'loai': r[2],
            'muc_gia': r[3], 'diem': float(r[4] or 0), 'so_luot': r[5],
            'dia_chi': r[6], 'kinh_do': float(r[7] or 0), 'vi_do': float(r[8] or 0)
        } for r in c.fetchall()]
    return JsonResponse({'status': 'success', 'data': data})


def api_timkiem(request):
    """API: Tìm quán theo vị trí và bán kính"""
    lat = float(request.GET.get('lat', 10.78))
    lng = float(request.GET.get('lng', 106.70))
    r = float(request.GET.get('r', 2)) * 1000  # km -> m
    
    sql = f"""
    SELECT q.ma_quan, q.ten_quan, l.ten_loai, q.muc_gia, q.diem_danh_gia,
           ST_X(q.vi_tri), ST_Y(q.vi_tri),
           ST_Distance(q.vi_tri::geography, ST_SetSRID(ST_MakePoint({lng},{lat}),4326)::geography)/1000
    FROM quan_an q LEFT JOIN loai_quan l ON q.ma_loai = l.ma_loai
    WHERE ST_DWithin(q.vi_tri::geography, ST_SetSRID(ST_MakePoint({lng},{lat}),4326)::geography, {r})
    ORDER BY 8
    """
    with connection.cursor() as c:
        c.execute(sql)
        data = [{
            'ma_quan': r[0], 'ten_quan': r[1], 'loai': r[2],
            'muc_gia': r[3], 'diem': float(r[4] or 0),
            'kinh_do': float(r[5] or 0), 'vi_do': float(r[6] or 0), 
            'khoang_cach': round(float(r[7] or 0), 2)
        } for r in c.fetchall()]
    return JsonResponse({'status': 'success', 'data': data})


def api_goiy(request, ma_quan):
    """API: Gợi ý quán tương tự - CÙNG LOẠI"""
    top = int(request.GET.get('top', 5))
    
    # Lấy loại của quán hiện tại
    with connection.cursor() as c:
        c.execute("SELECT ma_loai FROM quan_an WHERE ma_quan = %s", [ma_quan])
        row = c.fetchone()
    
    if not row:
        return JsonResponse({'status': 'error', 'data': []})
    
    ma_loai = row[0]
    
    # Gợi ý quán CÙNG LOẠI, sắp xếp theo điểm
    sql = """
    SELECT q.ma_quan, q.ten_quan, l.ten_loai, q.muc_gia, q.diem_danh_gia,
           ST_X(q.vi_tri), ST_Y(q.vi_tri)
    FROM quan_an q 
    LEFT JOIN loai_quan l ON q.ma_loai = l.ma_loai
    WHERE q.ma_quan != %s AND q.ma_loai = %s
    ORDER BY q.diem_danh_gia DESC
    LIMIT %s
    """
    with connection.cursor() as c:
        c.execute(sql, [ma_quan, ma_loai, top])
        data = [{
            'ma_quan': r[0], 'ten_quan': r[1], 'loai': r[2],
            'muc_gia': r[3], 'diem': float(r[4] or 0),
            'kinh_do': float(r[5] or 0), 'vi_do': float(r[6] or 0)
        } for r in c.fetchall()]
    
    return JsonResponse({'status': 'success', 'data': data})
