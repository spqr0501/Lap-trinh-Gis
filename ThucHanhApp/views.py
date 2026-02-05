from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from .models import LoaiCuaHang, CuaHang, DanhGia, SuKien, CuaHangSuKien
from .utils.gis_tools import CongCuGIS, khoang_cach_km
from functools import wraps



# Decorator for admin views
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Vui lòng đăng nhập để truy cập trang này')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ====== PUBLIC VIEWS ======

def trang_chu(request):
    """Home page with integrated map, routing, sidebar, and GIS tools"""
    cua_hangs = CuaHang.objects.select_related('loai').prefetch_related('su_kiens__su_kien').all()
    loai_cua_hangs = LoaiCuaHang.objects.all()
    
    # Prepare store data with events
    stores_data = []
    for ch in cua_hangs:
        events = [cs.su_kien for cs in ch.su_kiens.all()]
        stores_data.append({
            'store': ch,
            'events': events,
            'has_events': len(events) > 0
        })
    
    return render(request, 'bando.html', {
        'stores_data': stores_data,
        'loai_cua_hangs': loai_cua_hangs,
    })


# ====== GIS TOOLS API ======

def api_gis_tools(request):
    """
    API endpoint demonstrating custom GIS tools
    Example usage: /api/gis-tools/?tool=distance&lat1=16.05&lon1=108.20&lat2=16.06&lon2=108.21
    """
    tool = request.GET.get('tool', '')
    
    try:
        if tool == 'distance':
            # Calculate distance between two points
            lat1 = float(request.GET.get('lat1'))
            lon1 = float(request.GET.get('lon1'))
            lat2 = float(request.GET.get('lat2'))
            lon2 = float(request.GET.get('lon2'))
            
            khoang_cach = khoang_cach_km(lat1, lon1, lat2, lon2)
            
            return JsonResponse({
                'success': True,
                'tool': 'distance',
                'result': {
                    'distance_km': round(khoang_cach, 3),
                    'distance_m': round(khoang_cach * 1000, 1)
                }
            })
        
        elif tool == 'nearest':
            # Find nearest store to a point
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
            
            stores = CuaHang.objects.filter(geom__isnull=False)
            points = [(s.geom.y, s.geom.x, s) for s in stores]
            
            gan_nhat, khoang_cach_nho_nhat = CongCuGIS.tim_diem_gan_nhat(lat, lon, points)
            
            if gan_nhat:
                cua_hang = gan_nhat[2]
                return JsonResponse({
                    'success': True,
                    'tool': 'nearest',
                    'result': {
                        'store_id': cua_hang.id,
                        'store_name': cua_hang.ten_cua_hang,
                        'distance_km': round(khoang_cach_nho_nhat, 3)
                    }
                })
        
        elif tool == 'buffer':
            # Create buffer zone around a point
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
            radius_km = float(request.GET.get('radius', 1.0))
            
            diem_vung_dem = CongCuGIS.tao_vung_dem_hinh_tron(lat, lon, radius_km)
            
            return JsonResponse({
                'success': True,
                'tool': 'buffer',
                'result': {
                    'center': [lat, lon],
                    'radius_km': radius_km,
                    'polygon': diem_vung_dem
                }
            })
        
        elif tool == 'centroid':
            # Calculate centroid of all stores
            stores = CuaHang.objects.filter(geom__isnull=False)
            points = [(s.geom.y, s.geom.x) for s in stores]
            
            if points:
                vi_do_tam, kinh_do_tam = CongCuGIS.tinh_diem_trung_tam(points)
                
                return JsonResponse({
                    'success': True,
                    'tool': 'centroid',
                    'result': {
                        'centroid': [vi_do_tam, kinh_do_tam],
                        'num_stores': len(points)
                    }
                })
        
        elif tool == 'within_radius':
            # Find stores within radius
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
            radius_km = float(request.GET.get('radius', 5.0))
            
            stores = CuaHang.objects.filter(geom__isnull=False)
            points = [(s.geom.y, s.geom.x, s) for s in stores]
            
            ket_qua = CongCuGIS.tim_diem_trong_ban_kinh(lat, lon, points, radius_km)
            
            stores_list = [{
                'store_id': r['diem'][2].id,
                'store_name': r['diem'][2].ten_cua_hang,
                'distance_km': round(r['khoang_cach'], 3)
            } for r in ket_qua]
            
            return JsonResponse({
                'success': True,
                'tool': 'within_radius',
                'result': {
                    'origin': [lat, lon],
                    'radius_km': radius_km,
                    'count': len(stores_list),
                    'stores': stores_list
                }
            })
        
        elif tool == 'bearing':
            # Calculate bearing between two points
            lat1 = float(request.GET.get('lat1'))
            lon1 = float(request.GET.get('lon1'))
            lat2 = float(request.GET.get('lat2'))
            lon2 = float(request.GET.get('lon2'))
            
            huong_di = CongCuGIS.tinh_huong_di(lat1, lon1, lat2, lon2)
            
            # Convert bearing to direction
            directions = ['Bắc', 'Đông Bắc', 'Đông', 'Đông Nam', 
                         'Nam', 'Tây Nam', 'Tây', 'Tây Bắc']
            direction = directions[int((huong_di + 22.5) // 45) % 8]
            
            return JsonResponse({
                'success': True,
                'tool': 'bearing',
                'result': {
                    'bearing_degrees': round(huong_di, 1),
                    'direction': direction
                }
            })
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'Unknown tool. Available: distance, nearest, buffer, centroid, within_radius, bearing'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



# ====== ADMIN AUTHENTICATION ======

def admin_login(request):
    """Admin login"""
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Đăng nhập thành công!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
    
    return render(request, 'admin/admin_login.html')


def admin_logout(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'Đã đăng xuất')
    return redirect('trang_chu')


@admin_required
def admin_dashboard(request):
    """Admin dashboard with statistics"""
    stats = {
        'loai_count': LoaiCuaHang.objects.count(),
        'cuahang_count': CuaHang.objects.count(),
        'danhgia_count': DanhGia.objects.count(),
        'sukien_count': SuKien.objects.count(),
    }
    recent_reviews = DanhGia.objects.select_related('cua_hang').order_by('-ngay_danh_gia')[:5]
    
    return render(request, 'admin/admin_dashboard.html', {
        'stats': stats,
        'recent_reviews': recent_reviews
    })


# ====== ADMIN CRUD: LOAI CUA HANG ======

@admin_required
def admin_loai_list(request):
    """List all store types"""
    items = LoaiCuaHang.objects.all()
    return render(request, 'admin/loai_list.html', {'items': items})


@admin_required
def admin_loai_create(request):
    """Create new store type"""
    if request.method == 'POST':
        ten_loai = request.POST.get('ten_loai')
        mo_ta = request.POST.get('mo_ta', '')
        
        LoaiCuaHang.objects.create(
            ten_loai=ten_loai,
            mo_ta=mo_ta
        )
        messages.success(request, 'Thêm loại cửa hàng thành công!')
        return redirect('admin_loai_list')
    
    return render(request, 'admin/loai_form.html')


@admin_required
def admin_loai_update(request, id):
    """Update store type"""
    item = get_object_or_404(LoaiCuaHang, id=id)
    
    if request.method == 'POST':
        item.ten_loai = request.POST.get('ten_loai')
        item.mo_ta = request.POST.get('mo_ta', '')
        item.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_loai_list')
    
    return render(request, 'admin/loai_form.html', {'item': item})


@admin_required
def admin_loai_delete(request, id):
    """Delete store type"""
    item = get_object_or_404(LoaiCuaHang, id=id)
    item.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_loai_list')


# ====== ADMIN CRUD: CUA HANG ======

@admin_required
def admin_cuahang_list(request):
    """List all stores"""
    items = CuaHang.objects.select_related('loai').all()
    return render(request, 'admin/cuahang_list.html', {'items': items})


@admin_required
def admin_cuahang_create(request):
    """Create new store"""
    if request.method == 'POST':
        ten_cua_hang = request.POST.get('ten_cua_hang')
        dia_chi = request.POST.get('dia_chi')
        loai_id = request.POST.get('loai_id')
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        
        loai = get_object_or_404(LoaiCuaHang, id=loai_id)
        
        geom = None
        if lat and lng:
            geom = Point(float(lng), float(lat), srid=4326)
        
        CuaHang.objects.create(
            ten_cua_hang=ten_cua_hang,
            dia_chi=dia_chi,
            loai=loai,
            geom=geom
        )
        messages.success(request, 'Thêm cửa hàng thành công!')
        return redirect('admin_cuahang_list')
    
    loai_cua_hangs = LoaiCuaHang.objects.all()
    return render(request, 'admin/cuahang_form.html', {'loai_cua_hangs': loai_cua_hangs})


@admin_required
def admin_cuahang_update(request, id):
    """Update store"""
    item = get_object_or_404(CuaHang, id=id)
    
    if request.method == 'POST':
        item.ten_cua_hang = request.POST.get('ten_cua_hang')
        item.dia_chi = request.POST.get('dia_chi')
        item.loai = get_object_or_404(LoaiCuaHang, id=request.POST.get('loai_id'))
        
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        if lat and lng:
            item.geom = Point(float(lng), float(lat), srid=4326)
        
        item.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_cuahang_list')
    
    loai_cua_hangs = LoaiCuaHang.objects.all()
    return render(request, 'admin/cuahang_form.html', {
        'item': item,
        'loai_cua_hangs': loai_cua_hangs
    })


@admin_required
def admin_cuahang_delete(request, id):
    """Delete store"""
    item = get_object_or_404(CuaHang, id=id)
    item.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_cuahang_list')


# ====== ADMIN CRUD: DANH GIA ======

@admin_required
def admin_danhgia_list(request):
    """List all reviews"""
    items = DanhGia.objects.select_related('cua_hang').all()
    return render(request, 'admin/danhgia_list.html', {'items': items})


@admin_required
def admin_danhgia_create(request):
    """Create new review"""
    if request.method == 'POST':
        cua_hang_id = request.POST.get('cua_hang_id')
        diem = request.POST.get('diem')
        nhan_xet = request.POST.get('nhan_xet', '')
        ngay_danh_gia = request.POST.get('ngay_danh_gia')
        
        cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
        
        DanhGia.objects.create(
            cua_hang=cua_hang,
            diem=int(diem),
            nhan_xet=nhan_xet,
            ngay_danh_gia=ngay_danh_gia
        )
        messages.success(request, 'Thêm đánh giá thành công!')
        return redirect('admin_danhgia_list')
    
    cua_hangs = CuaHang.objects.all()
    return render(request, 'admin/danhgia_form.html', {'cua_hangs': cua_hangs})


@admin_required
def admin_danhgia_update(request, id):
    """Update review"""
    item = get_object_or_404(DanhGia, id=id)
    
    if request.method == 'POST':
        item.cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        item.diem = int(request.POST.get('diem'))
        item.nhan_xet = request.POST.get('nhan_xet', '')
        item.ngay_danh_gia = request.POST.get('ngay_danh_gia')
        item.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_danhgia_list')
    
    cua_hangs = CuaHang.objects.all()
    return render(request, 'admin/danhgia_form.html', {
        'item': item,
        'cua_hangs': cua_hangs
    })


@admin_required
def admin_danhgia_delete(request, id):
    """Delete review"""
    item = get_object_or_404(DanhGia, id=id)
    item.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_danhgia_list')


# ====== ADMIN CRUD: SU KIEN ======

@admin_required
def admin_sukien_list(request):
    """List all events"""
    items = SuKien.objects.all()
    return render(request, 'admin/sukien_list.html', {'items': items})


@admin_required
def admin_sukien_create(request):
    """Create new event"""
    if request.method == 'POST':
        ten_su_kien = request.POST.get('ten_su_kien')
        mo_ta = request.POST.get('mo_ta', '')
        ngay_bat_dau = request.POST.get('ngay_bat_dau')
        ngay_ket_thuc = request.POST.get('ngay_ket_thuc')
        
        SuKien.objects.create(
            ten_su_kien=ten_su_kien,
            mo_ta=mo_ta,
            ngay_bat_dau=ngay_bat_dau,
            ngay_ket_thuc=ngay_ket_thuc
        )
        messages.success(request, 'Thêm sự kiện thành công!')
        return redirect('admin_sukien_list')
    
    return render(request, 'admin/sukien_form.html')


@admin_required
def admin_sukien_update(request, id):
    """Update event"""
    item = get_object_or_404(SuKien, id=id)
    
    if request.method == 'POST':
        item.ten_su_kien = request.POST.get('ten_su_kien')
        item.mo_ta = request.POST.get('mo_ta', '')
        item.ngay_bat_dau = request.POST.get('ngay_bat_dau')
        item.ngay_ket_thuc = request.POST.get('ngay_ket_thuc')
        item.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_sukien_list')
    
    return render(request, 'admin/sukien_form.html', {'item': item})


@admin_required
def admin_sukien_delete(request, id):
    """Delete event"""
    item = get_object_or_404(SuKien, id=id)
    item.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_sukien_list')


# ====== ADMIN CRUD: CUA HANG - SU KIEN ======

@admin_required
def admin_cuahang_sukien_list(request):
    """List all store-event relationships"""
    items = CuaHangSuKien.objects.select_related('cua_hang', 'su_kien').all()
    return render(request, 'admin/cuahang_sukien_list.html', {'items': items})


@admin_required
def admin_cuahang_sukien_create(request):
    """Create new store-event relationship"""
    if request.method == 'POST':
        cua_hang_id = request.POST.get('cua_hang_id')
        su_kien_id = request.POST.get('su_kien_id')
        
        cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
        su_kien = get_object_or_404(SuKien, id=su_kien_id)
        
        # Check if relationship already exists
        if not CuaHangSuKien.objects.filter(cua_hang=cua_hang, su_kien=su_kien).exists():
            CuaHangSuKien.objects.create(
                cua_hang=cua_hang,
                su_kien=su_kien
            )
            messages.success(request, 'Thêm thành công!')
        else:
            messages.warning(request, 'Quan hệ này đã tồn tại!')
        
        return redirect('admin_cuahang_sukien_list')
    
    cua_hangs = CuaHang.objects.all()
    su_kiens = SuKien.objects.all()
    return render(request, 'admin/cuahang_sukien_form.html', {
        'cua_hangs': cua_hangs,
        'su_kiens': su_kiens
    })


@admin_required
def admin_cuahang_sukien_delete(request, id):
    """Delete store-event relationship"""
    item = get_object_or_404(CuaHangSuKien, id=id)
    item.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_cuahang_sukien_list')
