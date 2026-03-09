from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from .models import LoaiCuaHang, CuaHang, DanhGia, SuKien, CuaHangSuKien, MatHang, TonKho, DonHang, ChiTietDonHang
from django.contrib.auth.models import User
from .utils.gis_tools import CongCuGIS, khoang_cach_km
from functools import wraps


# Decorator cho cac view danh cho admin
def admin_required(view_func):
    """
    Decorator kiem tra quyen truy cap admin
    
    GIAI THICH:
    - Kiem tra xem nguoi dung da dang nhap chua
    - Neu chua dang nhap, chuyen huong ve trang dang nhap admin
    - Neu da dang nhap, cho phep truy cap view
    - Su dung decorator @wraps de giu nguyen metadata cua ham goc
    
    THAM SO:
        view_func: Ham view can duoc bao ve
    
    TRA VE:
        Ham wrapper da duoc bao ve
        
    VI DU:
        >>> @admin_required
        >>> def admin_dashboard(request):
        ...     return render(request, 'admin/dashboard.html')
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Vui lòng đăng nhập để truy cập trang này')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ====== CAC VIEW CONG KHAI ======

def trang_chu(request):
    """
    Trang chu voi ban do tich hop, dinh tuyen, thanh ben va cac cong cu GIS
    
    GIAI THICH:
    - Hien thi trang chu voi ban do tuong tac
    - Lay danh sach tat ca cua hang va loai cua hang
    - Tich hop thong tin su kien cho tung cua hang
    - Chuan bi du lieu de hien thi tren ban do va sidebar
    - Su dung select_related va prefetch_related de toi uu query
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse voi template 'bando.html' va context du lieu
        
    VI DU:
        Truy cap: http://localhost:8000/
        Hien thi ban do voi tat ca cua hang, chuc nang tim duong, v.v.
    """
    # Lay danh sach cua hang voi cac quan he lien ket
    danh_sach_cua_hang = CuaHang.objects.select_related('loai').prefetch_related('su_kiens__su_kien').all()
    danh_sach_loai = LoaiCuaHang.objects.all()
    
    # Chuan bi du lieu cua hang kem theo su kien
    du_lieu_cua_hang = []
    for cua_hang in danh_sach_cua_hang:
        danh_sach_su_kien = [cs.su_kien for cs in cua_hang.su_kiens.all()]
        du_lieu_cua_hang.append({
            'store': cua_hang,
            'events': danh_sach_su_kien,
            'has_events': len(danh_sach_su_kien) > 0
        })
    
    return render(request, 'bando.html', {
        'stores_data': du_lieu_cua_hang,
        'loai_cua_hangs': danh_sach_loai,
    })


# ====== API DANH GIA ======

def api_danh_gia(request, cua_hang_id):
    """Tra ve danh sach danh gia cua mot cua hang dang JSON"""
    cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
    danh_gias = DanhGia.objects.filter(cua_hang=cua_hang).order_by('-ngay_danh_gia')

    ds = []
    for dg in danh_gias:
        ds.append({
            'diem': dg.diem,
            'nhan_xet': dg.nhan_xet,
            'ngay': dg.ngay_danh_gia.strftime('%d/%m/%Y'),
        })

    trung_binh = sum(d['diem'] for d in ds) / len(ds) if ds else 0

    return JsonResponse({
        'ten_cua_hang': cua_hang.ten_cua_hang,
        'so_danh_gia': len(ds),
        'trung_binh': round(trung_binh, 1),
        'danh_gias': ds,
    })


def api_gui_danh_gia(request, cua_hang_id):
    """Tiep nhan danh gia moi (POST) cho mot cua hang"""
    if request.method != 'POST':
        return JsonResponse({'loi': 'Chi chap nhan POST'}, status=405)

    import json
    from datetime import date
    try:
        du_lieu = json.loads(request.body)
        diem = int(du_lieu.get('diem', 0))
        nhan_xet = du_lieu.get('nhan_xet', '').strip()
        if not (1 <= diem <= 5):
            return JsonResponse({'loi': 'Diem phai tu 1 den 5'}, status=400)
        cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
        danh_gia = DanhGia.objects.create(
            cua_hang=cua_hang,
            diem=diem,
            nhan_xet=nhan_xet,
            ngay_danh_gia=date.today(),
            nguoi_dung=request.user if request.user.is_authenticated else None
        )
        ten_nguoi = request.user.get_full_name() or request.user.username if request.user.is_authenticated else 'Ẩn danh'
        return JsonResponse({'thanh_cong': True, 'ten_nguoi': ten_nguoi})
    except Exception as e:
        return JsonResponse({'loi': str(e)}, status=400)


# ====== API CONG CU GIS ======

def api_gis_tools(request):
    """
    API endpoint demo cac cong cu GIS tu viet
    
    GIAI THICH:
    - Cung cap cac endpoint API de su dung cong cu GIS
    - Ho tro cac chuc nang: tinh khoang cach, tim gan nhat, tao vung dem,
      tinh diem trung tam, tim trong ban kinh, tinh huong di
    - Nhan tham so qua query string va tra ve ket qua dang JSON
    - Su dung cac ham tu lop CongCuGIS (khong dung thu vien ben ngoai)
    
    THAM SO:
        request: Django HttpRequest object
        Query params:
            tool: Ten cong cu (distance, nearest, buffer, centroid, within_radius, bearing)
            Tham so khac tuy thuoc vao cong cu cu the
    
    TRA VE:
        JsonResponse voi ket qua tinh toan hoac thong bao loi
        
    VI DU:
        >>> # Tinh khoang cach giua 2 diem
        >>> GET /api/gis-tools/?tool=distance&lat1=16.05&lon1=108.20&lat2=16.06&lon2=108.21
        >>> # Tim cua hang gan nhat
        >>> GET /api/gis-tools/?tool=nearest&lat=16.05&lon=108.20
    """
    cong_cu = request.GET.get('tool', '')
    
    try:
        if cong_cu == 'distance':
            # Tinh khoang cach giua 2 diem
            vi_do_1 = float(request.GET.get('lat1'))
            kinh_do_1 = float(request.GET.get('lon1'))
            vi_do_2 = float(request.GET.get('lat2'))
            kinh_do_2 = float(request.GET.get('lon2'))
            
            khoang_cach = khoang_cach_km(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2)
            
            return JsonResponse({
                'success': True,
                'tool': 'distance',
                'result': {
                    'distance_km': round(khoang_cach, 3),
                    'distance_m': round(khoang_cach * 1000, 1)
                }
            })
        
        elif cong_cu == 'nearest':
            # Tim cua hang gan nhat tu mot diem
            vi_do = float(request.GET.get('lat'))
            kinh_do = float(request.GET.get('lon'))
            
            danh_sach_cua_hang = CuaHang.objects.filter(geom__isnull=False)
            danh_sach_diem = [(ch.geom.y, ch.geom.x, ch) for ch in danh_sach_cua_hang]
            
            gan_nhat, khoang_cach_nho_nhat = CongCuGIS.tim_diem_gan_nhat(vi_do, kinh_do, danh_sach_diem)
            
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
        
        elif cong_cu == 'buffer':
            # Tao vung dem hinh tron xung quanh mot diem
            vi_do = float(request.GET.get('lat'))
            kinh_do = float(request.GET.get('lon'))
            ban_kinh_km = float(request.GET.get('radius', 1.0))
            
            diem_vung_dem = CongCuGIS.tao_vung_dem_hinh_tron(vi_do, kinh_do, ban_kinh_km)
            
            return JsonResponse({
                'success': True,
                'tool': 'buffer',
                'result': {
                    'center': [vi_do, kinh_do],
                    'radius_km': ban_kinh_km,
                    'polygon': diem_vung_dem
                }
            })
        
        elif cong_cu == 'centroid':
            # Tinh diem trung tam cua tat ca cua hang
            danh_sach_cua_hang = CuaHang.objects.filter(geom__isnull=False)
            danh_sach_diem = [(ch.geom.y, ch.geom.x) for ch in danh_sach_cua_hang]
            
            if danh_sach_diem:
                vi_do_tam, kinh_do_tam = CongCuGIS.tinh_diem_trung_tam(danh_sach_diem)
                
                return JsonResponse({
                    'success': True,
                    'tool': 'centroid',
                    'result': {
                        'centroid': [vi_do_tam, kinh_do_tam],
                        'num_stores': len(danh_sach_diem)
                    }
                })
        
        elif cong_cu == 'within_radius':
            # Tim cua hang trong ban kinh cho truoc
            vi_do = float(request.GET.get('lat'))
            kinh_do = float(request.GET.get('lon'))
            ban_kinh_km = float(request.GET.get('radius', 5.0))
            
            danh_sach_cua_hang = CuaHang.objects.filter(geom__isnull=False)
            danh_sach_diem = [(ch.geom.y, ch.geom.x, ch) for ch in danh_sach_cua_hang]
            
            ket_qua = CongCuGIS.tim_diem_trong_ban_kinh(vi_do, kinh_do, danh_sach_diem, ban_kinh_km)
            
            danh_sach_ket_qua = [{
                'store_id': r['diem'][2].id,
                'store_name': r['diem'][2].ten_cua_hang,
                'distance_km': round(r['khoang_cach'], 3)
            } for r in ket_qua]
            
            return JsonResponse({
                'success': True,
                'tool': 'within_radius',
                'result': {
                    'origin': [vi_do, kinh_do],
                    'radius_km': ban_kinh_km,
                    'count': len(danh_sach_ket_qua),
                    'stores': danh_sach_ket_qua
                }
            })
        
        elif cong_cu == 'bearing':
            # Tinh huong di giua 2 diem
            vi_do_1 = float(request.GET.get('lat1'))
            kinh_do_1 = float(request.GET.get('lon1'))
            vi_do_2 = float(request.GET.get('lat2'))
            kinh_do_2 = float(request.GET.get('lon2'))
            
            huong_di = CongCuGIS.tinh_huong_di(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2)
            
            # Chuyen doi goc thanh huong (8 huong chinh)
            cac_huong = ['Bắc', 'Đông Bắc', 'Đông', 'Đông Nam', 
                         'Nam', 'Tây Nam', 'Tây', 'Tây Bắc']
            huong = cac_huong[int((huong_di + 22.5) // 45) % 8]
            
            return JsonResponse({
                'success': True,
                'tool': 'bearing',
                'result': {
                    'bearing_degrees': round(huong_di, 1),
                    'direction': huong
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



# ====== XAC THUC ADMIN ======

def admin_login(request):
    """
    Trang dang nhap danh cho quan tri vien
    
    GIAI THICH:
    - Neu da dang nhap, chuyen huong den trang dashboard
    - Xu ly form dang nhap qua POST request
    - Su dung Django authenticate de xac thuc nguoi dung
    - Hien thi thong bao loi neu dang nhap that bai
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse - Redirect den dashboard neu thanh cong,
        hoac render form dang nhap neu chua dang nhap
        
    VI DU:
        POST /admin/login/ voi username va password
        Redirect den /admin/dashboard/ neu thanh cong
    """
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        ten_dang_nhap = request.POST.get('username')
        mat_khau = request.POST.get('password')
        nguoi_dung = authenticate(request, username=ten_dang_nhap, password=mat_khau)
        
        if nguoi_dung is not None:
            login(request, nguoi_dung)
            messages.success(request, 'Đăng nhập thành công!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
    
    return render(request, 'admin/admin_login.html')


def admin_logout(request):
    """
    Dang xuat quan tri vien
    
    GIAI THICH:
    - Dang xuat nguoi dung hien tai
    - Hien thi thong bao thanh cong
    - Chuyen huong ve trang chu
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse - Redirect ve trang chu
        
    VI DU:
        GET /admin/logout/
        Dang xuat va chuyen ve trang chu
    """
    logout(request)
    messages.success(request, 'Đã đăng xuất')
    return redirect('trang_chu')


@admin_required
def admin_dashboard(request):
    """
    Trang tong quan danh cho quan tri vien voi cac thong ke
    
    GIAI THICH:
    - Hien thi cac thong ke tong quat: so luong loai cua hang, cua hang, danh gia, su kien
    - Hien thi 5 danh gia gan day nhat
    - Chi danh cho nguoi dung da dang nhap (su dung decorator @admin_required)
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse voi template admin_dashboard.html va context thong ke
        
    VI DU:
        GET /admin/dashboard/
        Hien thi dashboard voi cac so lieu thong ke
    """
    thong_ke = {
        'loai_count': LoaiCuaHang.objects.count(),
        'cuahang_count': CuaHang.objects.count(),
        'danhgia_count': DanhGia.objects.count(),
        'sukien_count': SuKien.objects.count(),
    }
    danh_gia_gan_day = DanhGia.objects.select_related('cua_hang').order_by('-ngay_danh_gia')[:5]
    
    return render(request, 'admin/admin_dashboard.html', {
        'stats': thong_ke,
        'recent_reviews': danh_gia_gan_day
    })


# ====== ADMIN CRUD: LOAI CUA HANG ======

@admin_required
def admin_loai_list(request):
    """
    Hien thi danh sach tat ca loai cua hang
    
    GIAI THICH:
    - Lay tat ca cac loai cua hang tu database
    - Hien thi duoi dang bang danh sach
    - Chi danh cho admin da dang nhap
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse voi template loai_list.html
        
    VI DU:
        GET /admin/loai/
        Hien thi danh sach tat ca loai cua hang
    """
    danh_sach_muc = LoaiCuaHang.objects.all()
    return render(request, 'admin/loai_list.html', {'items': danh_sach_muc})


@admin_required
def admin_loai_create(request):
    """
    Tao loai cua hang moi
    
    GIAI THICH:
    - Hien thi form nhap lieu cho loai cua hang moi
    - Xu ly POST request de luu loai cua hang vao database
    - Hien thi thong bao thanh cong va chuyen den trang danh sach
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse - Form neu GET, redirect den danh sach neu POST thanh cong
        
    VI DU:
        GET /admin/loai/create/ - Hien thi form
        POST /admin/loai/create/ - Tao moi va redirect
    """
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
    """
    Cap nhat thong tin loai cua hang
    
    GIAI THICH:
    - Lay loai cua hang theo ID
    - Hien thi form voi du lieu hien tai
    - Xu ly POST request de cap nhat thong tin
    - Hien thi loi 404 neu khong tim thay
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua loai cua hang can cap nhat
    
    TRA VE:
        HttpResponse - Form voi du lieu hien tai neu GET, redirect neu POST thanh cong
        
    VI DU:
        GET /admin/loai/update/1/ - Hien thi form cap nhat
        POST /admin/loai/update/1/ - Luu va redirect
    """
    muc = get_object_or_404(LoaiCuaHang, id=id)
    
    if request.method == 'POST':
        muc.ten_loai = request.POST.get('ten_loai')
        muc.mo_ta = request.POST.get('mo_ta', '')
        muc.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_loai_list')
    
    return render(request, 'admin/loai_form.html', {'item': muc})


@admin_required
def admin_loai_delete(request, id):
    """
    Xoa loai cua hang
    
    GIAI THICH:
    - Tim loai cua hang theo ID
    - Xoa khoi database
    - Hien thi thong bao thanh cong
    - Chuyen huong ve trang danh sach
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua loai cua hang can xoa
    
    TRA VE:
        HttpResponse - Redirect ve trang danh sach
        
    VI DU:
        GET/POST /admin/loai/delete/1/
        Xoa va chuyen ve danh sach
    """
    muc = get_object_or_404(LoaiCuaHang, id=id)
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_loai_list')


# ====== ADMIN CRUD: CUA HANG ======

@admin_required
def admin_cuahang_list(request):
    """
    Hien thi danh sach tat ca cua hang
    
    GIAI THICH:
    - Lay tat ca cua hang tu database
    - Su dung select_related de toi uu query voi loai cua hang
    - Hien thi duoi dang bang danh sach
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse voi template cuahang_list.html
        
    VI DU:
        GET /admin/cuahang/
        Hien thi danh sach tat ca cua hang
    """
    danh_sach_muc = CuaHang.objects.select_related('loai').all()
    return render(request, 'admin/cuahang_list.html', {'items': danh_sach_muc})


@admin_required
def admin_cuahang_create(request):
    """
    Tao cua hang moi
    
    GIAI THICH:
    - Hien thi form nhap lieu cho cua hang moi
    - Xu ly POST request de luu cua hang vao database
    - Tao Point geometry tu toa do kinh vi do
    - Lien ket voi loai cua hang tuong ung
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse - Form neu GET, redirect den danh sach neu POST thanh cong
        
    VI DU:
        GET /admin/cuahang/create/ - Hien thi form
        POST /admin/cuahang/create/ - Tao moi va redirect
    """
    if request.method == 'POST':
        ten_cua_hang = request.POST.get('ten_cua_hang')
        dia_chi = request.POST.get('dia_chi')
        loai_id = request.POST.get('loai_id')
        vi_do = request.POST.get('lat')
        kinh_do = request.POST.get('lng')
        
        loai = get_object_or_404(LoaiCuaHang, id=loai_id)
        
        # Tao Point geometry neu co toa do
        geom = None
        if vi_do and kinh_do:
            geom = Point(float(kinh_do), float(vi_do), srid=4326)
        
        CuaHang.objects.create(
            ten_cua_hang=ten_cua_hang,
            dia_chi=dia_chi,
            loai=loai,
            geom=geom
        )
        messages.success(request, 'Thêm cửa hàng thành công!')
        return redirect('admin_cuahang_list')
    
    danh_sach_loai = LoaiCuaHang.objects.all()
    return render(request, 'admin/cuahang_form.html', {'loai_cua_hangs': danh_sach_loai})


@admin_required
def admin_cuahang_update(request, id):
    """
    Cap nhat thong tin cua hang
    
    GIAI THICH:
    - Lay cua hang theo ID
    - Hien thi form voi du lieu hien tai
    - Xu ly POST request de cap nhat thong tin
    - Cap nhat ca toa do geometry neu co thay doi
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua cua hang can cap nhat
    
    TRA VE:
        HttpResponse - Form voi du lieu hien tai neu GET, redirect neu POST thanh cong
        
    VI DU:
        GET /admin/cuahang/update/1/ - Hien thi form cap nhat
        POST /admin/cuahang/update/1/ - Luu va redirect
    """
    muc = get_object_or_404(CuaHang, id=id)
    
    if request.method == 'POST':
        muc.ten_cua_hang = request.POST.get('ten_cua_hang')
        muc.dia_chi = request.POST.get('dia_chi')
        muc.loai = get_object_or_404(LoaiCuaHang, id=request.POST.get('loai_id'))
        
        # Cap nhat toa do neu co
        vi_do = request.POST.get('lat')
        kinh_do = request.POST.get('lng')
        if vi_do and kinh_do:
            muc.geom = Point(float(kinh_do), float(vi_do), srid=4326)
        
        muc.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_cuahang_list')
    
    danh_sach_loai = LoaiCuaHang.objects.all()
    return render(request, 'admin/cuahang_form.html', {
        'item': muc,
        'loai_cua_hangs': danh_sach_loai
    })


@admin_required
def admin_cuahang_delete(request, id):
    """
    Xoa cua hang
    
    GIAI THICH:
    - Tim cua hang theo ID
    - Xoa khoi database (cascade se xoa ca cac lien ket)
    - Hien thi thong bao thanh cong
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua cua hang can xoa
    
    TRA VE:
        HttpResponse - Redirect ve trang danh sach
        
    VI DU:
        GET/POST /admin/cuahang/delete/1/
        Xoa va chuyen ve danh sach
    """
    muc = get_object_or_404(CuaHang, id=id)
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_cuahang_list')


# ====== ADMIN CRUD: DANH GIA ======

@admin_required
def admin_danhgia_list(request):
    """
    Hien thi danh sach tat ca danh gia
    
    GIAI THICH:
    - Lay tat ca danh gia tu database
    - Su dung select_related de toi uu query voi cua hang
    - Hien thi duoi dang bang danh sach
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse voi template danhgia_list.html
        
    VI DU:
        GET /admin/danhgia/
        Hien thi danh sach tat ca danh gia
    """
    danh_sach_muc = DanhGia.objects.select_related('cua_hang').all()
    return render(request, 'admin/danhgia_list.html', {'items': danh_sach_muc})


@admin_required
def admin_danhgia_create(request):
    """
    Tao danh gia moi cho cua hang
    
    GIAI THICH:
    - Hien thi form nhap lieu cho danh gia moi
    - Xu ly POST request de luu danh gia vao database
    - Yeu cau chon cua hang, diem danh gia, nhan xet va ngay danh gia
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse - Form neu GET, redirect den danh sach neu POST thanh cong
        
    VI DU:
        GET /admin/danhgia/create/ - Hien thi form
        POST /admin/danhgia/create/ - Tao moi va redirect
    """
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
    
    danh_sach_cua_hang = CuaHang.objects.all()
    return render(request, 'admin/danhgia_form.html', {'cua_hangs': danh_sach_cua_hang})


@admin_required
def admin_danhgia_update(request, id):
    """
    Cap nhat thong tin danh gia
    
    GIAI THICH:
    - Lay danh gia theo ID
    - Hien thi form voi du lieu hien tai
    - Xu ly POST request de cap nhat thong tin
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua danh gia can cap nhat
    
    TRA VE:
        HttpResponse - Form voi du lieu hien tai neu GET, redirect neu POST thanh cong
        
    VI DU:
        GET /admin/danhgia/update/1/ - Hien thi form cap nhat
        POST /admin/danhgia/update/1/ - Luu va redirect
    """
    muc = get_object_or_404(DanhGia, id=id)
    
    if request.method == 'POST':
        muc.cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        muc.diem = int(request.POST.get('diem'))
        muc.nhan_xet = request.POST.get('nhan_xet', '')
        muc.ngay_danh_gia = request.POST.get('ngay_danh_gia')
        muc.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_danhgia_list')
    
    danh_sach_cua_hang = CuaHang.objects.all()
    return render(request, 'admin/danhgia_form.html', {
        'item': muc,
        'cua_hangs': danh_sach_cua_hang
    })


@admin_required
def admin_danhgia_delete(request, id):
    """
    Xoa danh gia
    
    GIAI THICH:
    - Tim danh gia theo ID
    - Xoa khoi database
    - Hien thi thong bao thanh cong
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua danh gia can xoa
    
    TRA VE:
        HttpResponse - Redirect ve trang danh sach
        
    VI DU:
        GET/POST /admin/danhgia/delete/1/
        Xoa va chuyen ve danh sach
    """
    muc = get_object_or_404(DanhGia, id=id)
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_danhgia_list')


# ====== ADMIN CRUD: SU KIEN ======

@admin_required
def admin_sukien_list(request):
    """
    Hien thi danh sach tat ca su kien
    
    GIAI THICH:
    - Lay tat ca su kien tu database
    - Hien thi duoi dang bang danh sach
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse voi template sukien_list.html
        
    VI DU:
        GET /admin/sukien/
        Hien thi danh sach tat ca su kien
    """
    danh_sach_muc = SuKien.objects.all()
    return render(request, 'admin/sukien_list.html', {'items': danh_sach_muc})


@admin_required
def admin_sukien_create(request):
    """
    Tao su kien moi
    
    GIAI THICH:
    - Hien thi form nhap lieu cho su kien moi
    - Xu ly POST request de luu su kien vao database
    - Yeu cau ten su kien, mo ta, ngay bat dau va ket thuc
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse - Form neu GET, redirect den danh sach neu POST thanh cong
        
    VI DU:
        GET /admin/sukien/create/ - Hien thi form
        POST /admin/sukien/create/ - Tao moi va redirect
    """
    if request.method == 'POST':
        ten_su_kien = request.POST.get('ten_su_kien')
        mo_ta = request.POST.get('mo_ta', '')
        ngay_bat_dau = request.POST.get('ngay_bat_dau')
        ngay_ket_thuc = request.POST.get('ngay_ket_thuc')
        la_hang_tuan = 'la_hang_tuan' in request.POST
        ngay_trong_tuan_list = request.POST.getlist('ngay_trong_tuan')
        ngay_trong_tuan = ','.join(ngay_trong_tuan_list)
        cua_hang_id = request.POST.get('cua_hang')

        su_kien = SuKien.objects.create(
            ten_su_kien=ten_su_kien,
            mo_ta=mo_ta,
            ngay_bat_dau=ngay_bat_dau,
            ngay_ket_thuc=ngay_ket_thuc,
            la_hang_tuan=la_hang_tuan,
            ngay_trong_tuan=ngay_trong_tuan
        )
        # Lien ket voi cua hang
        if cua_hang_id:
            CuaHangSuKien.objects.get_or_create(
                cua_hang_id=cua_hang_id,
                su_kien=su_kien
            )
        messages.success(request, 'Thêm sự kiện thành công!')
        return redirect('admin_sukien_list')

    stores = CuaHang.objects.all()
    ngay_choices = SuKien.NGAY_TRONG_TUAN
    return render(request, 'admin/sukien_form.html', {
        'stores': stores,
        'ngay_choices': ngay_choices,
        'ngay_da_chon': [],
    })


@admin_required
def admin_sukien_update(request, id):
    """
    Cap nhat thong tin su kien
    
    GIAI THICH:
    - Lay su kien theo ID
    - Hien thi form voi du lieu hien tai
    - Xu ly POST request de cap nhat thong tin
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua su kien can cap nhat
    
    TRA VE:
        HttpResponse - Form voi du lieu hien tai neu GET, redirect neu POST thanh cong
        
    VI DU:
        GET /admin/sukien/update/1/ - Hien thi form cap nhat
        POST /admin/sukien/update/1/ - Luu va redirect
    """
    muc = get_object_or_404(SuKien, id=id)
    
    if request.method == 'POST':
        muc.ten_su_kien = request.POST.get('ten_su_kien')
        muc.mo_ta = request.POST.get('mo_ta', '')
        muc.ngay_bat_dau = request.POST.get('ngay_bat_dau')
        muc.ngay_ket_thuc = request.POST.get('ngay_ket_thuc')
        muc.la_hang_tuan = 'la_hang_tuan' in request.POST
        ngay_trong_tuan_list = request.POST.getlist('ngay_trong_tuan')
        muc.ngay_trong_tuan = ','.join(ngay_trong_tuan_list)
        muc.save()
        # Cap nhat lien ket cua hang
        cua_hang_id = request.POST.get('cua_hang')
        if cua_hang_id:
            muc.cua_hangs.all().delete()
            CuaHangSuKien.objects.create(
                cua_hang_id=cua_hang_id,
                su_kien=muc
            )
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_sukien_list')

    stores = CuaHang.objects.all()
    cua_hang_hien_tai = muc.cua_hangs.first()
    ngay_choices = SuKien.NGAY_TRONG_TUAN
    ngay_da_chon = muc.get_ngay_trong_tuan_list()
    return render(request, 'admin/sukien_form.html', {
        'item': muc,
        'stores': stores,
        'cua_hang_hien_tai': cua_hang_hien_tai,
        'ngay_choices': ngay_choices,
        'ngay_da_chon': ngay_da_chon,
    })


@admin_required
def admin_sukien_delete(request, id):
    """
    Xoa su kien
    
    GIAI THICH:
    - Tim su kien theo ID
    - Xoa khoi database
    - Hien thi thong bao thanh cong
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua su kien can xoa
    
    TRA VE:
        HttpResponse - Redirect ve trang danh sach
        
    VI DU:
        GET/POST /admin/sukien/delete/1/
        Xoa va chuyen ve danh sach
    """
    muc = get_object_or_404(SuKien, id=id)
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_sukien_list')


# ====== ADMIN CRUD: CUA HANG - SU KIEN ======

@admin_required
def admin_cuahang_sukien_list(request):
    """
    Hien thi danh sach tat ca quan he cua hang - su kien
    
    GIAI THICH:
    - Lay tat ca quan he many-to-many giua cua hang va su kien
    - Su dung select_related de toi uu query
    - Hien thi duoi dang bang danh sach
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse voi template cuahang_sukien_list.html
        
    VI DU:
        GET /admin/cuahang-sukien/
        Hien thi danh sach lien ket cua hang va su kien
    """
    danh_sach_muc = CuaHangSuKien.objects.select_related('cua_hang', 'su_kien').all()
    return render(request, 'admin/cuahang_sukien_list.html', {'items': danh_sach_muc})


@admin_required
def admin_cuahang_sukien_create(request):
    """
    Tao quan he cua hang - su kien moi
    
    GIAI THICH:
    - Hien thi form de chon cua hang va su kien
    - Xu ly POST request de tao lien ket
    - Kiem tra trung lap truoc khi tao
    - Hien thi canh bao neu quan he da ton tai
    
    THAM SO:
        request: Django HttpRequest object
    
    TRA VE:
        HttpResponse - Form neu GET, redirect den danh sach neu POST thanh cong
        
    VI DU:
        GET /admin/cuahang-sukien/create/ - Hien thi form
        POST /admin/cuahang-sukien/create/ - Tao lien ket va redirect
    """
    if request.method == 'POST':
        cua_hang_id = request.POST.get('cua_hang_id')
        su_kien_id = request.POST.get('su_kien_id')
        
        cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
        su_kien = get_object_or_404(SuKien, id=su_kien_id)
        
        # Kiem tra xem quan he da ton tai chua
        if not CuaHangSuKien.objects.filter(cua_hang=cua_hang, su_kien=su_kien).exists():
            CuaHangSuKien.objects.create(
                cua_hang=cua_hang,
                su_kien=su_kien
            )
            messages.success(request, 'Thêm thành công!')
        else:
            messages.warning(request, 'Quan hệ này đã tồn tại!')
        
        return redirect('admin_cuahang_sukien_list')
    
    danh_sach_cua_hang = CuaHang.objects.all()
    danh_sach_su_kien = SuKien.objects.all()
    return render(request, 'admin/cuahang_sukien_form.html', {
        'cua_hangs': danh_sach_cua_hang,
        'su_kiens': danh_sach_su_kien
    })


@admin_required
def admin_cuahang_sukien_delete(request, id):
    """
    Xoa quan he cua hang - su kien
    
    GIAI THICH:
    - Tim quan he theo ID
    - Xoa lien ket (khong xoa cua hang hay su kien)
    - Hien thi thong bao thanh cong
    
    THAM SO:
        request: Django HttpRequest object
        id: ID cua quan he can xoa
    
    TRA VE:
        HttpResponse - Redirect ve trang danh sach
        
    VI DU:
        GET/POST /admin/cuahang-sukien/delete/1/
        Xoa lien ket va chuyen ve danh sach
    """
    muc = get_object_or_404(CuaHangSuKien, id=id)
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_cuahang_sukien_list')


# ====== ADMIN CRUD: MAT HANG ======

@admin_required
def admin_mathang_list(request):
    items = MatHang.objects.all()
    return render(request, 'admin/mathang_list.html', {'items': items})


@admin_required
def admin_mathang_create(request):
    if request.method == 'POST':
        MatHang.objects.create(
            ten_mat_hang=request.POST.get('ten_mat_hang'),
            don_vi=request.POST.get('don_vi', 'cái'),
            gia_ban=request.POST.get('gia_ban', 0),
            mo_ta=request.POST.get('mo_ta', ''),
        )
        messages.success(request, 'Thêm mặt hàng thành công!')
        return redirect('admin_mathang_list')
    return render(request, 'admin/mathang_form.html')


@admin_required
def admin_mathang_update(request, id):
    muc = get_object_or_404(MatHang, id=id)
    if request.method == 'POST':
        muc.ten_mat_hang = request.POST.get('ten_mat_hang')
        muc.don_vi = request.POST.get('don_vi', 'cái')
        muc.gia_ban = request.POST.get('gia_ban', 0)
        muc.mo_ta = request.POST.get('mo_ta', '')
        muc.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_mathang_list')
    return render(request, 'admin/mathang_form.html', {'item': muc})


@admin_required
def admin_mathang_delete(request, id):
    muc = get_object_or_404(MatHang, id=id)
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_mathang_list')


# ====== ADMIN CRUD: TON KHO ======

@admin_required
def admin_tonkho_list(request):
    items = TonKho.objects.select_related('cua_hang', 'mat_hang').all()
    cua_hang_id = request.GET.get('cua_hang', '')
    if cua_hang_id:
        items = items.filter(cua_hang_id=int(cua_hang_id))
    cua_hangs = CuaHang.objects.all()
    return render(request, 'admin/tonkho_list.html', {
        'items': items, 'cua_hangs': cua_hangs, 'cua_hang_id': cua_hang_id
    })


@admin_required
def admin_tonkho_create(request):
    if request.method == 'POST':
        cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        mat_hang = get_object_or_404(MatHang, id=request.POST.get('mat_hang_id'))
        so_luong = int(request.POST.get('so_luong', 0))
        ton_kho, created = TonKho.objects.get_or_create(
            cua_hang=cua_hang, mat_hang=mat_hang,
            defaults={'so_luong': so_luong}
        )
        if not created:
            ton_kho.so_luong += so_luong
            ton_kho.save()
        messages.success(request, 'Cập nhật tồn kho thành công!')
        return redirect('admin_tonkho_list')
    cua_hangs = CuaHang.objects.all()
    mat_hangs = MatHang.objects.all()
    return render(request, 'admin/tonkho_form.html', {
        'cua_hangs': cua_hangs, 'mat_hangs': mat_hangs
    })


@admin_required
def admin_tonkho_update(request, id):
    muc = get_object_or_404(TonKho, id=id)
    if request.method == 'POST':
        muc.cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        muc.mat_hang = get_object_or_404(MatHang, id=request.POST.get('mat_hang_id'))
        muc.so_luong = int(request.POST.get('so_luong', 0))
        muc.save()
        messages.success(request, 'Cập nhật thành công!')
        return redirect('admin_tonkho_list')
    cua_hangs = CuaHang.objects.all()
    mat_hangs = MatHang.objects.all()
    return render(request, 'admin/tonkho_form.html', {
        'item': muc, 'cua_hangs': cua_hangs, 'mat_hangs': mat_hangs
    })


@admin_required
def admin_tonkho_delete(request, id):
    muc = get_object_or_404(TonKho, id=id)
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_tonkho_list')


# ====== ADMIN CRUD: DON HANG ======

@admin_required
def admin_donhang_list(request):
    items = DonHang.objects.select_related('cua_hang').all()
    return render(request, 'admin/donhang_list.html', {'items': items})


@admin_required
def admin_donhang_create(request):
    if request.method == 'POST':
        cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        mat_hang_ids = request.POST.getlist('mat_hang_id')
        so_luongs = request.POST.getlist('so_luong_sp')
        don_gias = request.POST.getlist('don_gia_sp')

        # Kiem tra ton kho truoc khi tao don hang
        loi_ton_kho = []
        for i in range(len(mat_hang_ids)):
            if mat_hang_ids[i]:
                mh_id = int(mat_hang_ids[i])
                sl_dat = int(so_luongs[i]) if i < len(so_luongs) else 1
                mat_hang = MatHang.objects.filter(id=mh_id).first()
                ton_kho = TonKho.objects.filter(
                    cua_hang=cua_hang, mat_hang_id=mh_id
                ).first()
                so_luong_ton = ton_kho.so_luong if ton_kho else 0
                if sl_dat > so_luong_ton:
                    ten_mh = mat_hang.ten_mat_hang if mat_hang else f'MH#{mh_id}'
                    loi_ton_kho.append(
                        f'{ten_mh}: đặt {sl_dat} nhưng kho {cua_hang.ten_cua_hang} chỉ còn {so_luong_ton}'
                    )

        if loi_ton_kho:
            for loi in loi_ton_kho:
                messages.error(request, f'❌ Không đủ hàng - {loi}')
            cua_hangs = CuaHang.objects.all()
            mat_hangs = MatHang.objects.all()
            trang_thais = DonHang.TRANG_THAI_CHOICES
            return render(request, 'admin/donhang_form.html', {
                'cua_hangs': cua_hangs, 'mat_hangs': mat_hangs, 'trang_thais': trang_thais
            })

        # Tao don hang
        don_hang = DonHang.objects.create(
            cua_hang=cua_hang,
            trang_thai=request.POST.get('trang_thai', 'cho_xu_ly'),
            ghi_chu=request.POST.get('ghi_chu', ''),
        )
        for i in range(len(mat_hang_ids)):
            if mat_hang_ids[i]:
                ct = ChiTietDonHang.objects.create(
                    don_hang=don_hang,
                    mat_hang_id=int(mat_hang_ids[i]),
                    so_luong=int(so_luongs[i]) if i < len(so_luongs) else 1,
                    don_gia=int(don_gias[i]) if i < len(don_gias) else 0,
                )
                # Tru ton kho
                if don_hang.trang_thai == 'da_thanh_toan':
                    ton_kho = TonKho.objects.filter(
                        cua_hang=cua_hang, mat_hang_id=int(mat_hang_ids[i])
                    ).first()
                    if ton_kho:
                        ton_kho.so_luong = max(0, ton_kho.so_luong - ct.so_luong)
                        ton_kho.save()
        don_hang.cap_nhat_tong_tien()
        messages.success(request, 'Tạo đơn hàng thành công!')
        return redirect('admin_donhang_list')
    cua_hangs = CuaHang.objects.all()
    mat_hangs = MatHang.objects.all()
    trang_thais = DonHang.TRANG_THAI_CHOICES
    return render(request, 'admin/donhang_form.html', {
        'cua_hangs': cua_hangs, 'mat_hangs': mat_hangs, 'trang_thais': trang_thais
    })


@admin_required
def admin_donhang_detail(request, id):
    don_hang = get_object_or_404(DonHang, id=id)
    chi_tiets = don_hang.chi_tiets.select_related('mat_hang').all()
    return render(request, 'admin/donhang_detail.html', {
        'don_hang': don_hang, 'chi_tiets': chi_tiets
    })


@admin_required
def admin_donhang_update(request, id):
    don_hang = get_object_or_404(DonHang, id=id)
    if request.method == 'POST':
        old_trang_thai = don_hang.trang_thai
        don_hang.cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        don_hang.trang_thai = request.POST.get('trang_thai', 'cho_xu_ly')
        don_hang.ghi_chu = request.POST.get('ghi_chu', '')
        don_hang.save()
        # Tru ton kho khi chuyen sang da_thanh_toan
        if old_trang_thai != 'da_thanh_toan' and don_hang.trang_thai == 'da_thanh_toan':
            for ct in don_hang.chi_tiets.all():
                ton_kho = TonKho.objects.filter(
                    cua_hang=don_hang.cua_hang, mat_hang=ct.mat_hang
                ).first()
                if ton_kho:
                    ton_kho.so_luong = max(0, ton_kho.so_luong - ct.so_luong)
                    ton_kho.save()
        messages.success(request, 'Cập nhật đơn hàng thành công!')
        return redirect('admin_donhang_list')
    cua_hangs = CuaHang.objects.all()
    trang_thais = DonHang.TRANG_THAI_CHOICES
    return render(request, 'admin/donhang_form.html', {
        'item': don_hang, 'cua_hangs': cua_hangs, 'trang_thais': trang_thais
    })


@admin_required
def admin_donhang_delete(request, id):
    muc = get_object_or_404(DonHang, id=id)
    muc.delete()
    messages.success(request, 'Xóa đơn hàng thành công!')
    return redirect('admin_donhang_list')


# ====== DOANH THU ======

@admin_required
def admin_doanhthu(request):
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth

    # Loc theo nam
    nam = request.GET.get('nam', '')
    don_hangs = DonHang.objects.filter(trang_thai='da_thanh_toan')
    if nam:
        don_hangs = don_hangs.filter(ngay_dat__year=int(nam))

    # Doanh thu theo thang
    doanh_thu_thang = don_hangs.annotate(
        thang=TruncMonth('ngay_dat')
    ).values('thang').annotate(
        tong=Sum('tong_tien'),
        so_don=Count('id')
    ).order_by('-thang')

    # Doanh thu theo cua hang
    doanh_thu_cua_hang = don_hangs.values(
        'cua_hang__ten_cua_hang', 'cua_hang__id'
    ).annotate(
        tong=Sum('tong_tien'),
        so_don=Count('id')
    ).order_by('-tong')

    tong_doanh_thu = don_hangs.aggregate(tong=Sum('tong_tien'))['tong'] or 0
    tong_don_hang = don_hangs.count()

    # Lay danh sach nam co don hang
    danh_sach_nam = DonHang.objects.filter(
        trang_thai='da_thanh_toan'
    ).dates('ngay_dat', 'year', order='DESC')

    return render(request, 'admin/doanhthu.html', {
        'doanh_thu_thang': doanh_thu_thang,
        'doanh_thu_cua_hang': doanh_thu_cua_hang,
        'tong_doanh_thu': tong_doanh_thu,
        'tong_don_hang': tong_don_hang,
        'nam_hien_tai': nam,
        'danh_sach_nam': danh_sach_nam,
    })


@admin_required
def admin_doanhthu_chitiet(request):
    from django.db.models import Sum

    don_hangs = DonHang.objects.filter(trang_thai='da_thanh_toan').select_related('cua_hang')
    tieu_de = 'Chi Tiết Doanh Thu'

    # Loc theo thang (format: YYYY-MM)
    thang = request.GET.get('thang', '')
    if thang:
        parts = thang.split('-')
        if len(parts) == 2:
            don_hangs = don_hangs.filter(ngay_dat__year=int(parts[0]), ngay_dat__month=int(parts[1]))
            tieu_de = f'Chi Tiết Doanh Thu Tháng {parts[1]}/{parts[0]}'

    # Loc theo cua hang
    cua_hang_id = request.GET.get('cua_hang', '')
    if cua_hang_id:
        cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
        don_hangs = don_hangs.filter(cua_hang=cua_hang)
        tieu_de = f'Chi Tiết Doanh Thu - {cua_hang.ten_cua_hang}'

    tong_doanh_thu = don_hangs.aggregate(tong=Sum('tong_tien'))['tong'] or 0

    return render(request, 'admin/doanhthu_chitiet.html', {
        'don_hangs': don_hangs.order_by('-ngay_dat'),
        'tieu_de': tieu_de,
        'tong_doanh_thu': tong_doanh_thu,
    })


# ====== USER: DANG KY, DANG NHAP ======

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        ho_ten = request.POST.get('ho_ten', '').strip()
        email = request.POST.get('email', '').strip()

        if not username or not password:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin!')
        elif password != password2:
            messages.error(request, 'Mật khẩu nhập lại không khớp!')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại!')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
            )
            if ho_ten:
                parts = ho_ten.split(' ', 1)
                user.last_name = parts[0]
                user.first_name = parts[1] if len(parts) > 1 else ''
                user.save()
            login(request, user)
            messages.success(request, f'Đăng ký thành công! Chào {ho_ten or username}!')
            return redirect('trang_chu')
    return render(request, 'user/register.html')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('trang_chu')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Đăng nhập thành công!')
            next_url = request.GET.get('next', 'trang_chu')
            return redirect(next_url)
        else:
            messages.error(request, 'Sai tên đăng nhập hoặc mật khẩu!')
    return render(request, 'user/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'Đã đăng xuất!')
    return redirect('trang_chu')


# ====== USER: DAT HANG ======

@login_required(login_url='/dang-nhap/')
def user_dat_hang(request, cua_hang_id):
    cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
    # Lay san pham con ton kho tai cua hang nay
    ton_khos = TonKho.objects.filter(cua_hang=cua_hang, so_luong__gt=0).select_related('mat_hang')

    if request.method == 'POST':
        mat_hang_ids = request.POST.getlist('mat_hang_id')
        so_luongs = request.POST.getlist('so_luong_sp')

        # Kiem tra ton kho
        loi = []
        items = []
        for i in range(len(mat_hang_ids)):
            if mat_hang_ids[i]:
                mh_id = int(mat_hang_ids[i])
                sl = int(so_luongs[i]) if i < len(so_luongs) and so_luongs[i] else 1
                if sl <= 0:
                    continue
                tk = TonKho.objects.filter(cua_hang=cua_hang, mat_hang_id=mh_id).first()
                mh = MatHang.objects.filter(id=mh_id).first()
                if not tk or sl > tk.so_luong:
                    loi.append(f'{mh.ten_mat_hang if mh else "SP"}: chỉ còn {tk.so_luong if tk else 0}')
                else:
                    items.append((mh_id, sl, mh.gia_ban))

        if loi:
            for l in loi:
                messages.error(request, f'❌ {l}')
        elif not items:
            messages.error(request, 'Vui lòng chọn ít nhất 1 sản phẩm!')
        else:
            don_hang = DonHang.objects.create(
                cua_hang=cua_hang,
                nguoi_dung=request.user,
                trang_thai='cho_xu_ly',
                ghi_chu=request.POST.get('ghi_chu', ''),
            )
            for mh_id, sl, gia in items:
                ChiTietDonHang.objects.create(
                    don_hang=don_hang,
                    mat_hang_id=mh_id,
                    so_luong=sl,
                    don_gia=gia,
                )
            don_hang.cap_nhat_tong_tien()
            messages.success(request, f'Đặt hàng thành công! Mã đơn: DH-{don_hang.id}')
            return redirect('user_don_hang')

    return render(request, 'user/dat_hang.html', {
        'cua_hang': cua_hang,
        'ton_khos': ton_khos,
    })


@login_required(login_url='/dang-nhap/')
def user_don_hang(request):
    don_hangs = DonHang.objects.filter(nguoi_dung=request.user).select_related('cua_hang').order_by('-ngay_dat')
    return render(request, 'user/don_hang.html', {
        'don_hangs': don_hangs,
    })
