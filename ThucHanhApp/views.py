from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from .models import LoaiCuaHang, CuaHang, DanhGia, DanhGiaLike, DanhGiaAnh, SuKien, CuaHangSuKien, MatHang, TonKho, DonHang, ChiTietDonHang, AuditLog, AdminThongBao
from django.contrib.auth.models import User
from .utils.gis_tools import CongCuGIS, khoang_cach_km
from functools import wraps
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.urls import reverse
from django.utils import timezone
import math
import json
from django.core.paginator import Paginator
from django.db.models import Count, Q

# Dinh dang ten nguoi dung theo thu tu tieng Viet: Ho + Ten dem + Ten
def dinh_dang_ten_nguoi_dung(user):
    if not user:
        return 'Ẩn danh'

    ho = (user.last_name or '').strip()
    ten = (user.first_name or '').strip()

    if ho and ten:
        return f'{ho} {ten}'
    if ten:
        return ten
    if ho:
        return ho

    full = (user.get_full_name() or '').strip()
    return full or user.username


def ghi_nhat_ky(request, module, hanh_dong, mo_ta, doi_tuong='', doi_tuong_id=None, du_lieu_truoc=None, du_lieu_sau=None):
    ip = ''
    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
    except Exception:
        ip = ''
    AuditLog.objects.create(
        nguoi_dung=request.user if request.user.is_authenticated else None,
        module=module,
        hanh_dong=hanh_dong,
        mo_ta=mo_ta,
        ip_address=ip or '',
        doi_tuong=doi_tuong or '',
        doi_tuong_id=doi_tuong_id,
        du_lieu_truoc=du_lieu_truoc,
        du_lieu_sau=du_lieu_sau,
    )


def tao_thong_bao_admin_don_moi(don_hang):
    staff_users = User.objects.filter(is_staff=True, is_active=True).only('id')
    if not staff_users.exists():
        return
    tieu_de = f'🆕 Đơn hàng mới DH-{don_hang.id}'
    noi_dung = f'{don_hang.nguoi_dung.username if don_hang.nguoi_dung else "Khách"} vừa đặt đơn tại {don_hang.cua_hang.ten_cua_hang}'
    objs = []
    for u in staff_users:
        objs.append(AdminThongBao(
            nguoi_dung_id=u.id,
            don_hang=don_hang,
            tieu_de=tieu_de,
            noi_dung=noi_dung,
        ))
    AdminThongBao.objects.bulk_create(objs, ignore_conflicts=False)


def phan_trang_queryset(request, queryset, per_page=10):
    page_number = request.GET.get('page', 1)
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)
    return page_obj, page_obj.object_list

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
    danh_sach_cua_hang = CuaHang.objects.select_related('loai').prefetch_related('su_kiens__su_kien').annotate(
        so_don_thanh_toan=Count('don_hangs', filter=Q(don_hangs__trang_thai='da_thanh_toan'), distinct=True),
        so_danh_gia=Count('danh_gias', distinct=True)
    ).all()
    danh_sach_loai = LoaiCuaHang.objects.all()
    
    # Tinh phan bo sao cho tung cua hang (cho Map Chart)
    from django.db.models import Avg
    phan_bo_sao_all = {}
    for ch in danh_sach_cua_hang:
        danh_gias_ch = DanhGia.objects.filter(cua_hang=ch)
        phan_bo = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for dg in danh_gias_ch:
            if 1 <= dg.diem <= 5:
                phan_bo[dg.diem] += 1
        tong_dg = sum(phan_bo.values())
        diem_tb = round(sum(k * v for k, v in phan_bo.items()) / tong_dg, 1) if tong_dg > 0 else 0
        phan_bo_sao_all[ch.id] = {'phan_bo': phan_bo, 'diem_tb': diem_tb}
    
    # Chuan bi du lieu cua hang kem theo su kien
    du_lieu_cua_hang = []
    for cua_hang in danh_sach_cua_hang:
        danh_sach_su_kien = [cs.su_kien for cs in cua_hang.su_kiens.all() if cs.su_kien.dang_dien_ra]
        sao_data = phan_bo_sao_all.get(cua_hang.id, {'phan_bo': {1:0,2:0,3:0,4:0,5:0}, 'diem_tb': 0})
        du_lieu_cua_hang.append({
            'store': cua_hang,
            'events': danh_sach_su_kien,
            'has_events': len(danh_sach_su_kien) > 0,
            'order_count': cua_hang.so_don_thanh_toan or 0,
            'review_count': cua_hang.so_danh_gia or 0,
            'phan_bo_sao': sao_data['phan_bo'],
            'diem_tb': sao_data['diem_tb'],
        })
    
    admin_unread_count = 0
    admin_notifs = []
    if request.user.is_authenticated and request.user.is_staff:
        admin_unread_count = AdminThongBao.objects.filter(nguoi_dung=request.user, da_doc=False).count()
        admin_notifs = AdminThongBao.objects.filter(nguoi_dung=request.user).select_related('don_hang')[:8]

    return render(request, 'bando.html', {
        'stores_data': du_lieu_cua_hang,
        'loai_cua_hangs': danh_sach_loai,
        'admin_unread_count': admin_unread_count,
        'admin_notifs': admin_notifs,
    })


# ====== API DANH GIA ======

def api_danh_gia(request, cua_hang_id):
    """Tra ve danh sach danh gia cua mot cua hang dang JSON"""
    cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
    from django.db.models import Count
    danh_gias = DanhGia.objects.filter(cua_hang=cua_hang).select_related('nguoi_dung').prefetch_related('hinh_anhs').annotate(
        like_count=Count('likes')
    ).order_by('-like_count', '-ngay_danh_gia')

    ds = []
    phan_bo_sao = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(DanhGiaLike.objects.filter(
            nguoi_dung=request.user,
            danh_gia__cua_hang=cua_hang
        ).values_list('danh_gia_id', flat=True))
    for dg in danh_gias:
        ten_nguoi = dinh_dang_ten_nguoi_dung(dg.nguoi_dung)
        phan_bo_sao[dg.diem] = phan_bo_sao.get(dg.diem, 0) + 1
        ds_anh_obj = [
            {'id': a.id, 'url': request.build_absolute_uri(a.hinh_anh.url)}
            for a in dg.hinh_anhs.all() if a.hinh_anh
        ]
        ds.append({
            'id': dg.id,
            'diem': dg.diem,
            'nhan_xet': dg.nhan_xet,
            'ngay': dg.ngay_danh_gia.strftime('%d/%m/%Y'),
            'ten_nguoi': ten_nguoi,
            'so_like': int(getattr(dg, 'like_count', 0) or 0),
            'da_like': dg.id in liked_ids,
            'hinh_anhs': [x['url'] for x in ds_anh_obj],
            'hinh_anhs_obj': ds_anh_obj,
            'la_cua_toi': bool(request.user.is_authenticated and dg.nguoi_dung_id == request.user.id),
        })

    trung_binh = sum(d['diem'] for d in ds) / len(ds) if ds else 0

    return JsonResponse({
        'ten_cua_hang': cua_hang.ten_cua_hang,
        'so_danh_gia': len(ds),
        'trung_binh': round(trung_binh, 1),
        'danh_gias': ds,
        'phan_bo_sao': phan_bo_sao,
    })


@login_required(login_url='/dang-nhap/')
def api_like_danh_gia(request, danh_gia_id):
    if request.method != 'POST':
        return JsonResponse({'loi': 'Chi chap nhan POST'}, status=405)
    dg = get_object_or_404(DanhGia, id=danh_gia_id)
    like, created = DanhGiaLike.objects.get_or_create(danh_gia=dg, nguoi_dung=request.user)
    if not created:
        like.delete()
        da_like = False
    else:
        da_like = True
    so_like = DanhGiaLike.objects.filter(danh_gia=dg).count()
    return JsonResponse({'thanh_cong': True, 'da_like': da_like, 'so_like': so_like})


def api_gui_danh_gia(request, cua_hang_id):
    """Tiep nhan danh gia moi (POST) cho mot cua hang"""
    if request.method != 'POST':
        return JsonResponse({'loi': 'Chi chap nhan POST'}, status=405)

    from datetime import date
    try:
        du_lieu = {}
        if request.content_type and 'application/json' in request.content_type:
            du_lieu = json.loads(request.body or '{}')
        else:
            du_lieu = request.POST
        diem = int(du_lieu.get('diem', 0))
        nhan_xet = du_lieu.get('nhan_xet', '').strip()
        hinh_anh_uploads = request.FILES.getlist('hinh_anh')
        if not (1 <= diem <= 5):
            return JsonResponse({'loi': 'Diem phai tu 1 den 5'}, status=400)
        cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
        cap_nhat = False
        if request.user.is_authenticated:
            danh_gia = DanhGia.objects.filter(cua_hang=cua_hang, nguoi_dung=request.user).first()
            if danh_gia:
                danh_gia.diem = diem
                danh_gia.nhan_xet = nhan_xet
                danh_gia.ngay_danh_gia = date.today()
                danh_gia.save()
                cap_nhat = True
            else:
                danh_gia = DanhGia.objects.create(
                    cua_hang=cua_hang,
                    diem=diem,
                    nhan_xet=nhan_xet,
                    ngay_danh_gia=date.today(),
                    nguoi_dung=request.user
                )
        else:
            danh_gia = DanhGia.objects.create(
                cua_hang=cua_hang,
                diem=diem,
                nhan_xet=nhan_xet,
                ngay_danh_gia=date.today(),
                nguoi_dung=None
            )

        xoa_anh_ids_raw = du_lieu.get('xoa_anh_ids', '')
        xoa_anh_ids = []
        if xoa_anh_ids_raw:
            if isinstance(xoa_anh_ids_raw, str):
                xoa_anh_ids = [int(x) for x in xoa_anh_ids_raw.split(',') if x.strip().isdigit()]
            elif isinstance(xoa_anh_ids_raw, list):
                xoa_anh_ids = [int(x) for x in xoa_anh_ids_raw if str(x).isdigit()]

        if xoa_anh_ids:
            DanhGiaAnh.objects.filter(danh_gia=danh_gia, id__in=xoa_anh_ids).delete()

        anh_hien_tai = DanhGiaAnh.objects.filter(danh_gia=danh_gia).count()
        if anh_hien_tai + len(hinh_anh_uploads) > 3:
            return JsonResponse({'loi': 'Tổng số ảnh sau cập nhật không được vượt quá 3'}, status=400)

        for f in hinh_anh_uploads:
            DanhGiaAnh.objects.create(danh_gia=danh_gia, hinh_anh=f)
        ten_nguoi = dinh_dang_ten_nguoi_dung(request.user if request.user.is_authenticated else None)
        ghi_nhat_ky(
            request,
            module='Đánh giá',
            hanh_dong='update' if cap_nhat else 'create',
            mo_ta=f"{'Cập nhật' if cap_nhat else 'Tạo'} đánh giá cho cửa hàng {cua_hang.ten_cua_hang} ({diem} sao)"
        )
        return JsonResponse({'thanh_cong': True, 'ten_nguoi': ten_nguoi, 'cap_nhat': cap_nhat})
    except Exception as e:
        return JsonResponse({'loi': str(e)}, status=400)


@login_required(login_url='/dang-nhap/')
def api_admin_thong_bao(request):
    if not request.user.is_staff:
        return JsonResponse({'loi': 'Không có quyền'}, status=403)
    qs = AdminThongBao.objects.filter(nguoi_dung=request.user).select_related('don_hang')[:8]
    unread_count = AdminThongBao.objects.filter(nguoi_dung=request.user, da_doc=False).count()
    items = []
    for tb in qs:
        url = reverse('admin_thong_bao_doc', args=[tb.id])
        items.append({
            'id': tb.id,
            'tieu_de': tb.tieu_de,
            'noi_dung': tb.noi_dung,
            'da_doc': tb.da_doc,
            'thoi_gian': tb.thoi_gian_tao.strftime('%H:%M %d/%m'),
            'url': url,
        })
    return JsonResponse({'unread_count': unread_count, 'items': items})


@login_required(login_url='/dang-nhap/')
def api_admin_thong_bao_doc(request, id):
    if request.method != 'POST':
        return JsonResponse({'loi': 'Chi chap nhan POST'}, status=405)
    if not request.user.is_staff:
        return JsonResponse({'loi': 'Không có quyền'}, status=403)
    tb = get_object_or_404(AdminThongBao, id=id, nguoi_dung=request.user)
    if not tb.da_doc:
        tb.da_doc = True
        tb.thoi_gian_doc = timezone.now()
        tb.save(update_fields=['da_doc', 'thoi_gian_doc'])
    url = reverse('admin_donhang_detail', args=[tb.don_hang_id]) if tb.don_hang_id else reverse('admin_thong_bao_list')
    return JsonResponse({'thanh_cong': True, 'url': url})


@login_required(login_url='/dang-nhap/')
def api_admin_thong_bao_doc_tat_ca(request):
    if request.method != 'POST':
        return JsonResponse({'loi': 'Chi chap nhan POST'}, status=405)
    if not request.user.is_staff:
        return JsonResponse({'loi': 'Không có quyền'}, status=403)
    AdminThongBao.objects.filter(nguoi_dung=request.user, da_doc=False).update(
        da_doc=True,
        thoi_gian_doc=timezone.now()
    )
    return JsonResponse({'thanh_cong': True})


@admin_required
def admin_thong_bao_list(request):
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền truy cập thông báo admin.')
        return redirect('trang_chu')
    qs = AdminThongBao.objects.filter(nguoi_dung=request.user).select_related('don_hang')
    page_obj, items = phan_trang_queryset(request, qs, per_page=20)
    return render(request, 'admin/thong_bao_list.html', {'items': items, 'page_obj': page_obj})


@admin_required
def admin_thong_bao_doc(request, id):
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền truy cập thông báo admin.')
        return redirect('trang_chu')
    tb = get_object_or_404(AdminThongBao, id=id, nguoi_dung=request.user)
    if not tb.da_doc:
        tb.da_doc = True
        tb.thoi_gian_doc = timezone.now()
        tb.save(update_fields=['da_doc', 'thoi_gian_doc'])
    if tb.don_hang_id:
        return redirect('admin_donhang_detail', id=tb.don_hang_id)
    return redirect('admin_thong_bao_list')


@admin_required
def admin_thong_bao_doc_tat_ca(request):
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền truy cập thông báo admin.')
        return redirect('trang_chu')
    AdminThongBao.objects.filter(nguoi_dung=request.user, da_doc=False).update(
        da_doc=True,
        thoi_gian_doc=timezone.now()
    )
    messages.success(request, 'Đã đánh dấu tất cả thông báo là đã đọc.')
    return redirect('trang_chu')


@admin_required
def admin_thong_bao_xoa_da_doc(request):
    if request.method != 'POST':
        return redirect('admin_thong_bao_list')
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền truy cập thông báo admin.')
        return redirect('trang_chu')
    so_xoa, _ = AdminThongBao.objects.filter(nguoi_dung=request.user, da_doc=True).delete()
    messages.success(request, f'Đã xóa {so_xoa} thông báo đã đọc.')
    return redirect('admin_thong_bao_list')


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
    from django.db.models import Count, Sum
    from django.utils import timezone

    thong_ke = {
        'loai_count': LoaiCuaHang.objects.count(),
        'cuahang_count': CuaHang.objects.count(),
        'danhgia_count': DanhGia.objects.count(),
        'sukien_count': SuKien.objects.count(),
    }
    danh_gia_gan_day = DanhGia.objects.select_related('cua_hang', 'nguoi_dung').order_by('-ngay_danh_gia')[:5]

    hom_nay = timezone.localdate()
    dau_thang = hom_nay.replace(day=1)

    don_hang_base = DonHang.objects.all()
    thong_ke_don_hang = {
        'tong': don_hang_base.count(),
        'hom_nay': don_hang_base.filter(ngay_dat__date=hom_nay).count(),
        'thang_nay': don_hang_base.filter(ngay_dat__date__gte=dau_thang).count(),
        'da_thanh_toan': don_hang_base.filter(trang_thai='da_thanh_toan').count(),
        'cho_xu_ly': don_hang_base.filter(trang_thai='cho_xu_ly').count(),
        'dang_giao': don_hang_base.filter(trang_thai='dang_giao').count(),
        'da_huy': don_hang_base.filter(trang_thai='da_huy').count(),
    }

    top_cua_hang_doanh_thu = DonHang.objects.filter(trang_thai='da_thanh_toan').values(
        'cua_hang__ten_cua_hang'
    ).annotate(
        tong=Sum('tong_tien'),
        so_don=Count('id')
    ).order_by('-tong')[:5]

    from django.db.models.functions import TruncMonth, TruncDate, TruncQuarter
    doanh_thu_6_thang = DonHang.objects.filter(trang_thai='da_thanh_toan').annotate(
        thang=TruncMonth('ngay_dat')
    ).values('thang').annotate(
        tong=Sum('tong_tien')
    ).order_by('-thang')[:6]
    doanh_thu_6_thang = list(reversed(list(doanh_thu_6_thang)))
    labels = [d['thang'].strftime('%m/%Y') for d in doanh_thu_6_thang]
    values = [int(d['tong'] or 0) for d in doanh_thu_6_thang]

    # Doanh thu 7 ngay gan nhat
    from datetime import timedelta
    ngay_7_truoc = hom_nay - timedelta(days=6)
    doanh_thu_7_ngay = DonHang.objects.filter(
        trang_thai='da_thanh_toan', ngay_dat__date__gte=ngay_7_truoc
    ).annotate(ngay=TruncDate('ngay_dat')).values('ngay').annotate(
        tong=Sum('tong_tien')
    ).order_by('ngay')
    # Tao du lieu day du 7 ngay (ke ca ngay khong co don)
    daily_map = {d['ngay']: int(d['tong'] or 0) for d in doanh_thu_7_ngay}
    daily_labels = []
    daily_values = []
    for i in range(7):
        ngay = ngay_7_truoc + timedelta(days=i)
        daily_labels.append(ngay.strftime('%d/%m'))
        daily_values.append(daily_map.get(ngay, 0))

    # Doanh thu theo quy (4 quy gan nhat)
    doanh_thu_quy = DonHang.objects.filter(trang_thai='da_thanh_toan').annotate(
        quy=TruncQuarter('ngay_dat')
    ).values('quy').annotate(
        tong=Sum('tong_tien')
    ).order_by('-quy')[:4]
    doanh_thu_quy = list(reversed(list(doanh_thu_quy)))
    quarter_labels = ['Q' + str((d['quy'].month - 1) // 3 + 1) + '/' + str(d['quy'].year) for d in doanh_thu_quy]
    quarter_values = [int(d['tong'] or 0) for d in doanh_thu_quy]

    # Diem danh gia trung binh tung cua hang (top 5)
    from django.db.models import Avg
    top_danh_gia = CuaHang.objects.annotate(
        diem_tb=Avg('danh_gias__diem'),
        so_dg=Count('danh_gias')
    ).filter(so_dg__gt=0).order_by('-diem_tb')[:5]
    rating_store_labels = [ch.ten_cua_hang for ch in top_danh_gia]
    rating_store_values = [round(float(ch.diem_tb or 0), 1) for ch in top_danh_gia]

    # Phan bo sao toan he thong
    phan_bo_sao_ht = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for dg in DanhGia.objects.all():
        if 1 <= dg.diem <= 5:
            phan_bo_sao_ht[dg.diem] += 1
    star_dist_values = [phan_bo_sao_ht[i] for i in range(1, 6)]

    return render(request, 'admin/admin_dashboard.html', {
        'stats': thong_ke,
        'recent_reviews': danh_gia_gan_day,
        'order_stats': thong_ke_don_hang,
        'top_store_revenue': top_cua_hang_doanh_thu,
        'chart_labels': labels,
        'chart_values': values,
        'daily_labels': daily_labels,
        'daily_values': daily_values,
        'quarter_labels': quarter_labels,
        'quarter_values': quarter_values,
        'rating_store_labels': rating_store_labels,
        'rating_store_values': rating_store_values,
        'star_dist_values': star_dist_values,
    })


@admin_required
def api_dashboard_revenue(request):
    """
    API tra ve du lieu doanh thu theo bo loc thoi gian
    Tham so GET: filter = 7ngay|30ngay|thang_truoc|quy_nay|nam_nay|nam_truoc|6thang|12thang
    """
    from django.http import JsonResponse
    from django.db.models import Sum
    from django.db.models.functions import TruncDate, TruncMonth, TruncQuarter
    from django.utils import timezone
    from datetime import timedelta
    import calendar

    bo_loc = request.GET.get('filter', '6thang')
    hom_nay = timezone.localdate()
    qs = DonHang.objects.filter(trang_thai='da_thanh_toan')
    labels = []
    values = []

    if bo_loc == '7ngay':
        bat_dau = hom_nay - timedelta(days=6)
        data = qs.filter(ngay_dat__date__gte=bat_dau).annotate(
            ngay=TruncDate('ngay_dat')
        ).values('ngay').annotate(tong=Sum('tong_tien')).order_by('ngay')
        data_map = {d['ngay']: int(d['tong'] or 0) for d in data}
        for i in range(7):
            ngay = bat_dau + timedelta(days=i)
            labels.append(ngay.strftime('%d/%m'))
            values.append(data_map.get(ngay, 0))

    elif bo_loc == '30ngay':
        bat_dau = hom_nay - timedelta(days=29)
        data = qs.filter(ngay_dat__date__gte=bat_dau).annotate(
            ngay=TruncDate('ngay_dat')
        ).values('ngay').annotate(tong=Sum('tong_tien')).order_by('ngay')
        data_map = {d['ngay']: int(d['tong'] or 0) for d in data}
        for i in range(30):
            ngay = bat_dau + timedelta(days=i)
            labels.append(ngay.strftime('%d/%m'))
            values.append(data_map.get(ngay, 0))

    elif bo_loc == 'thang_truoc':
        if hom_nay.month == 1:
            thang = 12
            nam = hom_nay.year - 1
        else:
            thang = hom_nay.month - 1
            nam = hom_nay.year
        so_ngay = calendar.monthrange(nam, thang)[1]
        from datetime import date
        bat_dau = date(nam, thang, 1)
        ket_thuc = date(nam, thang, so_ngay)
        data = qs.filter(ngay_dat__date__gte=bat_dau, ngay_dat__date__lte=ket_thuc).annotate(
            ngay=TruncDate('ngay_dat')
        ).values('ngay').annotate(tong=Sum('tong_tien')).order_by('ngay')
        data_map = {d['ngay']: int(d['tong'] or 0) for d in data}
        for i in range(so_ngay):
            ngay = bat_dau + timedelta(days=i)
            labels.append(ngay.strftime('%d/%m'))
            values.append(data_map.get(ngay, 0))

    elif bo_loc == 'quy_nay':
        quy_hien_tai = (hom_nay.month - 1) // 3 + 1
        thang_dau_quy = (quy_hien_tai - 1) * 3 + 1
        from datetime import date
        bat_dau = date(hom_nay.year, thang_dau_quy, 1)
        data = qs.filter(ngay_dat__date__gte=bat_dau, ngay_dat__date__lte=hom_nay).annotate(
            ngay=TruncDate('ngay_dat')
        ).values('ngay').annotate(tong=Sum('tong_tien')).order_by('ngay')
        data_map = {d['ngay']: int(d['tong'] or 0) for d in data}
        ngay_iter = bat_dau
        while ngay_iter <= hom_nay:
            labels.append(ngay_iter.strftime('%d/%m'))
            values.append(data_map.get(ngay_iter, 0))
            ngay_iter += timedelta(days=1)

    elif bo_loc == 'nam_nay':
        from datetime import date
        bat_dau = date(hom_nay.year, 1, 1)
        data = qs.filter(ngay_dat__date__gte=bat_dau).annotate(
            thang=TruncMonth('ngay_dat')
        ).values('thang').annotate(tong=Sum('tong_tien')).order_by('thang')
        data_map = {d['thang'].month: int(d['tong'] or 0) for d in data}
        for m in range(1, hom_nay.month + 1):
            labels.append(f'T{m}/{hom_nay.year}')
            values.append(data_map.get(m, 0))

    elif bo_loc == 'nam_truoc':
        nam_truoc = hom_nay.year - 1
        from datetime import date
        bat_dau = date(nam_truoc, 1, 1)
        ket_thuc = date(nam_truoc, 12, 31)
        data = qs.filter(ngay_dat__date__gte=bat_dau, ngay_dat__date__lte=ket_thuc).annotate(
            thang=TruncMonth('ngay_dat')
        ).values('thang').annotate(tong=Sum('tong_tien')).order_by('thang')
        data_map = {d['thang'].month: int(d['tong'] or 0) for d in data}
        for m in range(1, 13):
            labels.append(f'T{m}/{nam_truoc}')
            values.append(data_map.get(m, 0))

    elif bo_loc == '12thang':
        data = qs.annotate(thang=TruncMonth('ngay_dat')).values('thang').annotate(
            tong=Sum('tong_tien')
        ).order_by('-thang')[:12]
        data = list(reversed(list(data)))
        labels = [d['thang'].strftime('%m/%Y') for d in data]
        values = [int(d['tong'] or 0) for d in data]

    else:  # 6thang
        data = qs.annotate(thang=TruncMonth('ngay_dat')).values('thang').annotate(
            tong=Sum('tong_tien')
        ).order_by('-thang')[:6]
        data = list(reversed(list(data)))
        labels = [d['thang'].strftime('%m/%Y') for d in data]
        values = [int(d['tong'] or 0) for d in data]

    return JsonResponse({'labels': labels, 'values': values, 'filter': bo_loc})


@admin_required
def admin_audit_log(request):
    from datetime import datetime
    q = request.GET.get('q', '').strip()
    module = request.GET.get('module', '').strip()
    user_id = request.GET.get('user_id', '').strip()
    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()
    logs = AuditLog.objects.select_related('nguoi_dung').all()
    if module:
        logs = logs.filter(module=module)
    if user_id:
        logs = logs.filter(nguoi_dung_id=user_id)
    if tu_ngay:
        try:
            logs = logs.filter(thoi_gian__date__gte=datetime.strptime(tu_ngay, '%Y-%m-%d').date())
        except ValueError:
            pass
    if den_ngay:
        try:
            den = datetime.strptime(den_ngay, '%Y-%m-%d').date()
            logs = logs.filter(thoi_gian__date__lte=den)
        except ValueError:
            pass
    if q:
        logs = logs.filter(mo_ta__icontains=q)
    modules = AuditLog.objects.values_list('module', flat=True).distinct().order_by('module')
    users = User.objects.filter(audit_logs__isnull=False).distinct().order_by('username')
    page_obj, logs = phan_trang_queryset(request, logs, per_page=20)
    for log in logs:
        before = log.du_lieu_truoc or {}
        after = log.du_lieu_sau or {}
        if not isinstance(before, dict):
            before = {}
        if not isinstance(after, dict):
            after = {}
        keys = sorted(set(before.keys()) | set(after.keys()))
        log.diff_rows = []
        for key in keys:
            truoc = before.get(key, None)
            sau = after.get(key, None)
            if truoc != sau:
                log.diff_rows.append({
                    'key': key,
                    'truoc': '-' if truoc in [None, ''] else truoc,
                    'sau': '-' if sau in [None, ''] else sau,
                })
    return render(request, 'admin/audit_log.html', {
        'logs': logs,
        'page_obj': page_obj,
        'modules': modules,
        'users': users,
        'loc': {
            'q': q,
            'module': module,
            'user_id': user_id,
            'tu_ngay': tu_ngay,
            'den_ngay': den_ngay,
        },
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
    page_obj, items = phan_trang_queryset(request, danh_sach_muc, per_page=10)
    return render(request, 'admin/loai_list.html', {'items': items, 'page_obj': page_obj})


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
    page_obj, items = phan_trang_queryset(request, danh_sach_muc, per_page=10)
    return render(request, 'admin/cuahang_list.html', {'items': items, 'page_obj': page_obj})


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
    danh_sach_muc = DanhGia.objects.select_related('cua_hang', 'nguoi_dung').all()
    page_obj, items = phan_trang_queryset(request, danh_sach_muc, per_page=10)
    return render(request, 'admin/danhgia_list.html', {'items': items, 'page_obj': page_obj})


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
            ngay_danh_gia=ngay_danh_gia,
            # Admin tạo đánh giá thì vẫn lưu người tạo để hiển thị tên
            nguoi_dung=request.user if request.user.is_authenticated else None
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
    page_obj, items = phan_trang_queryset(request, danh_sach_muc, per_page=10)
    return render(request, 'admin/sukien_list.html', {'items': items, 'page_obj': page_obj})


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
    cua_hang_id = request.GET.get('cua_hang_id', '').strip()
    su_kien_id = request.GET.get('su_kien_id', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()

    if cua_hang_id:
        danh_sach_muc = danh_sach_muc.filter(cua_hang_id=cua_hang_id)
    if su_kien_id:
        danh_sach_muc = danh_sach_muc.filter(su_kien_id=su_kien_id)
    if trang_thai == 'dang_dien_ra':
        danh_sach_muc = [item for item in danh_sach_muc if item.su_kien.dang_dien_ra]
    elif trang_thai == 'sap_toi':
        from datetime import date
        hom_nay = date.today()
        danh_sach_muc = [item for item in danh_sach_muc if (not item.su_kien.la_hang_tuan and item.su_kien.ngay_bat_dau and item.su_kien.ngay_bat_dau > hom_nay)]

    page_obj, items = phan_trang_queryset(request, danh_sach_muc, per_page=10)
    return render(request, 'admin/cuahang_sukien_list.html', {
        'items': items,
        'page_obj': page_obj,
        'cua_hangs': CuaHang.objects.all(),
        'su_kiens': SuKien.objects.all(),
        'loc': {
            'cua_hang_id': cua_hang_id,
            'su_kien_id': su_kien_id,
            'trang_thai': trang_thai,
        }
    })


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
def admin_cuahang_sukien_update(request, id):
    muc = get_object_or_404(CuaHangSuKien, id=id)
    if request.method == 'POST':
        cua_hang_id = request.POST.get('cua_hang_id')
        su_kien_id = request.POST.get('su_kien_id')

        cua_hang = get_object_or_404(CuaHang, id=cua_hang_id)
        su_kien = get_object_or_404(SuKien, id=su_kien_id)

        da_ton_tai = CuaHangSuKien.objects.filter(
            cua_hang=cua_hang,
            su_kien=su_kien
        ).exclude(id=muc.id).exists()
        if da_ton_tai:
            messages.warning(request, 'Quan hệ này đã tồn tại!')
        else:
            muc.cua_hang = cua_hang
            muc.su_kien = su_kien
            muc.save()
            messages.success(request, 'Cập nhật thành công!')
            return redirect('admin_cuahang_sukien_list')

    return render(request, 'admin/cuahang_sukien_form.html', {
        'cua_hangs': CuaHang.objects.all(),
        'su_kiens': SuKien.objects.all(),
        'item': muc
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
    ds = MatHang.objects.all()
    page_obj, items = phan_trang_queryset(request, ds, per_page=10)
    return render(request, 'admin/mathang_list.html', {'items': items, 'page_obj': page_obj})


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
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    items = TonKho.objects.select_related('cua_hang', 'mat_hang').all()
    cua_hang_id = request.GET.get('cua_hang', '')
    trang_thai = request.GET.get('trang_thai', '').strip()
    if cua_hang_id:
        items = items.filter(cua_hang_id=int(cua_hang_id))
    if trang_thai == 'het_hang':
        items = items.filter(so_luong=0)
    elif trang_thai == 'sap_het':
        items = items.filter(so_luong__gt=0, so_luong__lt=10)
    elif trang_thai == 'con_hang':
        items = items.filter(so_luong__gte=10)
    cua_hangs = CuaHang.objects.all()

    hom_nay = timezone.localdate()
    moc_7 = hom_nay - timedelta(days=7)
    moc_30 = hom_nay - timedelta(days=30)
    ds_7 = ChiTietDonHang.objects.filter(
        don_hang__trang_thai='da_thanh_toan',
        don_hang__ngay_dat__date__gte=moc_7
    ).values('don_hang__cua_hang_id', 'mat_hang_id').annotate(tong=Sum('so_luong'))
    ds_30 = ChiTietDonHang.objects.filter(
        don_hang__trang_thai='da_thanh_toan',
        don_hang__ngay_dat__date__gte=moc_30
    ).values('don_hang__cua_hang_id', 'mat_hang_id').annotate(tong=Sum('so_luong'))
    ban_7 = {(d['don_hang__cua_hang_id'], d['mat_hang_id']): d['tong'] or 0 for d in ds_7}
    ban_30 = {(d['don_hang__cua_hang_id'], d['mat_hang_id']): d['tong'] or 0 for d in ds_30}

    goi_y_nhap = []
    for tk in TonKho.objects.select_related('cua_hang', 'mat_hang').all():
        key = (tk.cua_hang_id, tk.mat_hang_id)
        avg7 = (ban_7.get(key, 0) / 7.0)
        avg30 = (ban_30.get(key, 0) / 30.0)
        toc_do = max(avg7, avg30)
        de_xuat = max(0, int(math.ceil(toc_do * 7 - tk.so_luong)))
        if de_xuat > 0:
            goi_y_nhap.append({
                'cua_hang': tk.cua_hang.ten_cua_hang,
                'mat_hang': tk.mat_hang.ten_mat_hang,
                'ton_hien_tai': tk.so_luong,
                'ban_tb_ngay': round(toc_do, 2),
                'de_xuat_nhap': de_xuat,
            })
    goi_y_nhap = sorted(goi_y_nhap, key=lambda x: x['de_xuat_nhap'], reverse=True)[:20]

    page_obj, page_items = phan_trang_queryset(request, items, per_page=10)
    return render(request, 'admin/tonkho_list.html', {
        'items': page_items,
        'page_obj': page_obj,
        'cua_hangs': cua_hangs,
        'cua_hang_id': cua_hang_id,
        'trang_thai': trang_thai,
        'goi_y_nhap': goi_y_nhap,
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
        ghi_nhat_ky(
            request,
            module='Tồn kho',
            hanh_dong='create' if created else 'update',
            mo_ta=f"{'Tạo' if created else 'Cộng thêm'} tồn kho {mat_hang.ten_mat_hang} tại {cua_hang.ten_cua_hang}, SL={so_luong}"
        )
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
        du_lieu_truoc = {
            'cua_hang': muc.cua_hang.ten_cua_hang,
            'mat_hang': muc.mat_hang.ten_mat_hang,
            'so_luong': muc.so_luong,
        }
        muc.cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        muc.mat_hang = get_object_or_404(MatHang, id=request.POST.get('mat_hang_id'))
        muc.so_luong = int(request.POST.get('so_luong', 0))
        muc.save()
        du_lieu_sau = {
            'cua_hang': muc.cua_hang.ten_cua_hang,
            'mat_hang': muc.mat_hang.ten_mat_hang,
            'so_luong': muc.so_luong,
        }
        ghi_nhat_ky(
            request,
            module='Tồn kho',
            hanh_dong='update',
            mo_ta=f"Cập nhật tồn kho {muc.mat_hang.ten_mat_hang} tại {muc.cua_hang.ten_cua_hang}",
            doi_tuong='TonKho',
            doi_tuong_id=muc.id,
            du_lieu_truoc=du_lieu_truoc,
            du_lieu_sau=du_lieu_sau
        )
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
    ghi_nhat_ky(
        request,
        module='Tồn kho',
        hanh_dong='delete',
        mo_ta=f"Xóa tồn kho {muc.mat_hang.ten_mat_hang} tại {muc.cua_hang.ten_cua_hang}"
    )
    muc.delete()
    messages.success(request, 'Xóa thành công!')
    return redirect('admin_tonkho_list')


@admin_required
def admin_tonkho_import_excel(request):
    """Nhap ton kho tu file Excel (.xlsx).

    Cot bat buoc: Ten cua hang | Ten mat hang | So luong
    - Tim cua hang / mat hang theo ten (case-insensitive, strip).
    - Neu da co ban ghi TonKho (cua_hang + mat_hang) -> cong them so_luong.
    - Neu chua co -> tao moi.
    """
    if request.method != 'POST':
        return redirect('admin_tonkho_list')

    file = request.FILES.get('excel_file')
    if not file:
        messages.error(request, 'Chưa chọn file!')
        return redirect('admin_tonkho_list')

    if not file.name.endswith(('.xlsx', '.xls')):
        messages.error(request, 'Chỉ hỗ trợ file .xlsx hoặc .xls!')
        return redirect('admin_tonkho_list')

    import openpyxl
    try:
        wb = openpyxl.load_workbook(file, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(min_row=2, values_only=True))  # bo dong tieu de
        if not rows:
            messages.warning(request, 'File Excel trống (không có dữ liệu)!')
            return redirect('admin_tonkho_list')

        # Cache ten -> obj
        ch_map = {ch.ten_cua_hang.strip().lower(): ch for ch in CuaHang.objects.all()}
        mh_map = {mh.ten_mat_hang.strip().lower(): mh for mh in MatHang.objects.all()}

        thanh_cong = 0
        loi = []
        for idx, row in enumerate(rows, start=2):
            if not row or len(row) < 3:
                loi.append(f'Dòng {idx}: thiếu cột')
                continue
            ten_ch = str(row[0] or '').strip()
            ten_mh = str(row[1] or '').strip()
            try:
                so_luong = int(row[2])
            except (TypeError, ValueError):
                loi.append(f'Dòng {idx}: số lượng không hợp lệ ({row[2]})')
                continue

            if so_luong < 0:
                loi.append(f'Dòng {idx}: số lượng âm ({so_luong})')
                continue

            cua_hang = ch_map.get(ten_ch.lower())
            if not cua_hang:
                loi.append(f'Dòng {idx}: không tìm thấy cửa hàng "{ten_ch}"')
                continue
            mat_hang = mh_map.get(ten_mh.lower())
            if not mat_hang:
                loi.append(f'Dòng {idx}: không tìm thấy mặt hàng "{ten_mh}"')
                continue

            ton_kho, created = TonKho.objects.get_or_create(
                cua_hang=cua_hang, mat_hang=mat_hang,
                defaults={'so_luong': so_luong}
            )
            if not created:
                ton_kho.so_luong += so_luong
                ton_kho.save()
            thanh_cong += 1

        ghi_nhat_ky(
            request,
            module='Tồn kho',
            hanh_dong='import',
            mo_ta=f"Nhập Excel tồn kho: {thanh_cong} dòng thành công, {len(loi)} lỗi"
        )

        if thanh_cong:
            messages.success(request, f'Nhập thành công {thanh_cong} dòng từ Excel!')
        for l in loi[:10]:  # gioi han hien thi 10 loi
            messages.error(request, l)
        if len(loi) > 10:
            messages.warning(request, f'... và {len(loi) - 10} lỗi khác.')

    except Exception as e:
        messages.error(request, f'Lỗi đọc file Excel: {e}')

    return redirect('admin_tonkho_list')


# ====== ADMIN CRUD: DON HANG ======

@admin_required
def admin_donhang_list(request):
    items = DonHang.objects.select_related('cua_hang', 'nguoi_dung').all()
    cua_hangs = CuaHang.objects.all()

    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()
    cua_hang_id = request.GET.get('cua_hang_id', '').strip()
    q = request.GET.get('q', '').strip()
    tong_tu = request.GET.get('tong_tu', '').strip()
    tong_den = request.GET.get('tong_den', '').strip()

    if trang_thai:
        items = items.filter(trang_thai=trang_thai)
    if cua_hang_id:
        items = items.filter(cua_hang_id=cua_hang_id)
    if tu_ngay:
        items = items.filter(ngay_dat__date__gte=tu_ngay)
    if den_ngay:
        items = items.filter(ngay_dat__date__lte=den_ngay)
    if q:
        ma = q.replace('DH-', '').strip()
        if ma.isdigit():
            items = items.filter(id=int(ma))
    if tong_tu:
        items = items.filter(tong_tien__gte=tong_tu)
    if tong_den:
        items = items.filter(tong_tien__lte=tong_den)

    sap_xep = request.GET.get('sap_xep', '-ngay_dat').strip() or '-ngay_dat'
    ds_sap_xep_hop_le = ['-ngay_dat', 'ngay_dat', '-tong_tien', 'tong_tien', '-id', 'id']
    if sap_xep in ds_sap_xep_hop_le:
        items = items.order_by(sap_xep)

    page_obj, page_items = phan_trang_queryset(request, items, per_page=12)

    return render(request, 'admin/donhang_list.html', {
        'items': page_items,
        'page_obj': page_obj,
        'cua_hangs': cua_hangs,
        'trang_thais': DonHang.TRANG_THAI_CHOICES,
        'loc': {
            'tu_ngay': tu_ngay,
            'den_ngay': den_ngay,
            'trang_thai': trang_thai,
            'cua_hang_id': cua_hang_id,
            'q': q,
            'tong_tu': tong_tu,
            'tong_den': tong_den,
            'sap_xep': sap_xep,
        }
    })


@admin_required
def admin_donhang_export_csv(request):
    import csv

    items = DonHang.objects.select_related('cua_hang', 'nguoi_dung').all()
    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()
    cua_hang_id = request.GET.get('cua_hang_id', '').strip()
    q = request.GET.get('q', '').strip()
    tong_tu = request.GET.get('tong_tu', '').strip()
    tong_den = request.GET.get('tong_den', '').strip()
    sap_xep = request.GET.get('sap_xep', '-ngay_dat').strip() or '-ngay_dat'

    if trang_thai:
        items = items.filter(trang_thai=trang_thai)
    if cua_hang_id:
        items = items.filter(cua_hang_id=cua_hang_id)
    if tu_ngay:
        items = items.filter(ngay_dat__date__gte=tu_ngay)
    if den_ngay:
        items = items.filter(ngay_dat__date__lte=den_ngay)
    if q:
        ma = q.replace('DH-', '').strip()
        if ma.isdigit():
            items = items.filter(id=int(ma))
    if tong_tu:
        items = items.filter(tong_tien__gte=tong_tu)
    if tong_den:
        items = items.filter(tong_tien__lte=tong_den)
    if sap_xep in ['-ngay_dat', 'ngay_dat', '-tong_tien', 'tong_tien', '-id', 'id']:
        items = items.order_by(sap_xep)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="don_hang.csv"'
    writer = csv.writer(response)
    writer.writerow(['Ma don', 'Cua hang', 'Nguoi dat', 'Ngay dat', 'Trang thai', 'Tong tien'])
    for item in items:
        writer.writerow([
            f'DH-{item.id}',
            item.cua_hang.ten_cua_hang,
            dinh_dang_ten_nguoi_dung(item.nguoi_dung),
            item.ngay_dat.strftime('%d/%m/%Y %H:%M'),
            item.get_trang_thai_display(),
            int(item.tong_tien),
        ])

    ghi_nhat_ky(
        request,
        module='Đơn hàng',
        hanh_dong='export',
        mo_ta='Xuất CSV danh sách đơn hàng theo bộ lọc'
    )
    return response


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
            nguoi_dung=request.user if request.user.is_authenticated else None,
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
        ghi_nhat_ky(
            request,
            module='Đơn hàng',
            hanh_dong='create',
            mo_ta=f"Tạo đơn hàng DH-{don_hang.id} tại {cua_hang.ten_cua_hang}, tổng {int(don_hang.tong_tien)} đ"
        )
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
    ghi_nhat_ky(
        request,
        module='Đơn hàng',
        hanh_dong='view',
        mo_ta=f"Xem chi tiết đơn hàng DH-{don_hang.id}"
    )
    return render(request, 'admin/donhang_detail.html', {
        'don_hang': don_hang, 'chi_tiets': chi_tiets
    })


@admin_required
def admin_donhang_update(request, id):
    don_hang = get_object_or_404(DonHang, id=id)
    if request.method == 'POST':
        old_trang_thai = don_hang.trang_thai
        du_lieu_truoc = {
            'cua_hang': don_hang.cua_hang.ten_cua_hang,
            'trang_thai': don_hang.get_trang_thai_display(),
            'ghi_chu': don_hang.ghi_chu or '',
            'tong_tien': int(don_hang.tong_tien or 0),
        }
        don_hang.cua_hang = get_object_or_404(CuaHang, id=request.POST.get('cua_hang_id'))
        don_hang.trang_thai = request.POST.get('trang_thai', 'cho_xu_ly')
        don_hang.ghi_chu = request.POST.get('ghi_chu', '')
        don_hang.save()
        du_lieu_sau = {
            'cua_hang': don_hang.cua_hang.ten_cua_hang,
            'trang_thai': don_hang.get_trang_thai_display(),
            'ghi_chu': don_hang.ghi_chu or '',
            'tong_tien': int(don_hang.tong_tien or 0),
        }
        # Tru ton kho khi chuyen sang da_thanh_toan
        if old_trang_thai != 'da_thanh_toan' and don_hang.trang_thai == 'da_thanh_toan':
            for ct in don_hang.chi_tiets.all():
                ton_kho = TonKho.objects.filter(
                    cua_hang=don_hang.cua_hang, mat_hang=ct.mat_hang
                ).first()
                if ton_kho:
                    ton_kho.so_luong = max(0, ton_kho.so_luong - ct.so_luong)
                    ton_kho.save()
                    
        # Gửi email khi trạng thái đơn thay đổi (Mailtrap Sandbox / SMTP)
        if old_trang_thai != don_hang.trang_thai and don_hang.nguoi_dung and don_hang.nguoi_dung.email:
            try:
                ten_kh = don_hang.nguoi_dung.first_name or don_hang.nguoi_dung.username
                tt_display = don_hang.get_trang_thai_display()
                if don_hang.trang_thai == 'da_thanh_toan':
                    subject = f'[DH-{don_hang.id}] Giao hàng thành công — Đã thanh toán'
                    message = (
                        f'Xin chào {ten_kh},\n\n'
                        f'Đơn hàng DH-{don_hang.id} tại cửa hàng «{don_hang.cua_hang.ten_cua_hang}» '
                        f'đã được giao / hoàn tất và đánh dấu ĐÃ THANH TOÁN.\n\n'
                        f'Tổng tiền: {int(don_hang.tong_tien or 0):,} đ\n\n'
                        f'Cảm ơn bạn đã mua hàng. Hẹn gặp lại!\n'
                    )
                else:
                    subject = f'Cập nhật trạng thái đơn hàng [DH-{don_hang.id}]'
                    message = (
                        f'Xin chào {ten_kh},\n\n'
                        f'Đơn hàng DH-{don_hang.id} tại {don_hang.cua_hang.ten_cua_hang} '
                        f'vừa được cập nhật trạng thái.\n\n'
                        f'Trạng thái hiện tại: {tt_display}\n\n'
                        f'Cảm ơn bạn đã sử dụng hệ thống!\n'
                    )
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[don_hang.nguoi_dung.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Loi gui email cap nhat don hang: {e}")

        ghi_nhat_ky(
            request,
            module='Đơn hàng',
            hanh_dong='update',
            mo_ta=f"Cập nhật DH-{don_hang.id}: trạng thái {old_trang_thai} -> {don_hang.trang_thai}",
            doi_tuong='DonHang',
            doi_tuong_id=don_hang.id,
            du_lieu_truoc=du_lieu_truoc,
            du_lieu_sau=du_lieu_sau
        )
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
    ghi_nhat_ky(
        request,
        module='Đơn hàng',
        hanh_dong='delete',
        mo_ta=f"Xóa đơn hàng DH-{muc.id}"
    )
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
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại!')
        else:
            try:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                )
                if ho_ten:
                    user.first_name = ho_ten
                    user.save()
                login(request, user)
                
                # Gui email chao mung
                if email:
                    try:
                        send_mail(
                            subject='Chào mừng bạn đến với WebGIS Cửa Hàng!',
                            message=f'Xin chào {ho_ten or username},\n\nCảm ơn bạn đã đăng ký tài khoản trên hệ thống WebGIS Cửa Hàng của chúng tôi!\n\nChúc bạn có những trải nghiệm tuyệt vời cùng bản đồ GIS.',
                            from_email=django_settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        print(f"Loi gui email chao mung: {e}")

                messages.success(request, f'Đăng ký thành công! Chào {ho_ten or username}!')
                return redirect('trang_chu')
            except Exception:
                messages.error(request, 'Tên đăng nhập đã tồn tại!')
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
            ghi_nhat_ky(
                request,
                module='Đơn hàng',
                hanh_dong='create',
                mo_ta=f"Người dùng đặt đơn DH-{don_hang.id} tại {cua_hang.ten_cua_hang}, tổng {int(don_hang.tong_tien)} đ"
            )
            tao_thong_bao_admin_don_moi(don_hang)

            # Gui email don hang
            if request.user.email:
                try:
                    chi_tiet_list = []
                    for mh_id, sl, gia in items:
                        mh = MatHang.objects.filter(id=mh_id).first()
                        ten_mh = mh.ten_mat_hang if mh else f"Sản phẩm #{mh_id}"
                        chi_tiet_list.append(f"- {ten_mh} (SL: {sl}): {gia * sl:,.0f} đ")
                    chi_tiet_str = "\n".join(chi_tiet_list)

                    send_mail(
                        subject=f'Xác nhận đặt hàng thành công [DH-{don_hang.id}]',
                        message=(
                            f'Xin chào {request.user.first_name or request.user.username},\n\n'
                            f'Bạn đã đặt hàng thành công tại {cua_hang.ten_cua_hang}.\n\n'
                            f'Chi tiết đơn hàng:\n{chi_tiet_str}\n\n'
                            f'Tổng tiền: {don_hang.tong_tien:,.0f} đ\n\n'
                            f'Đơn đang ở trạng thái «Chờ xử lý». Chúng tôi sẽ thông báo khi giao hàng hoàn tất.\n\n'
                            f'Cảm ơn bạn đã tin tưởng dịch vụ!\n'
                        ),
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[request.user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Loi gui email don hang: {e}")

            messages.success(request, f'Đặt hàng thành công! Mã đơn: DH-{don_hang.id}')
            return redirect('user_don_hang')

    return render(request, 'user/dat_hang.html', {
        'cua_hang': cua_hang,
        'ton_khos': ton_khos,
    })


@login_required(login_url='/dang-nhap/')
def user_don_hang(request):
    don_hangs = DonHang.objects.filter(nguoi_dung=request.user).select_related('cua_hang').order_by('-ngay_dat')
    review_history = DanhGia.objects.filter(nguoi_dung=request.user).select_related('cua_hang').order_by('-ngay_danh_gia')[:50]
    return render(request, 'user/don_hang.html', {
        'don_hangs': don_hangs,
        'review_history': review_history,
    })


@login_required(login_url='/dang-nhap/')
def api_user_donhang_detail(request, id):
    """API tra ve JSON chi tiet don hang cua user (cho in PDF)"""
    don_hang = get_object_or_404(DonHang, id=id, nguoi_dung=request.user)
    chi_tiets = don_hang.chi_tiets.select_related('mat_hang').all()
    data = {
        'id': don_hang.id,
        'cua_hang': don_hang.cua_hang.ten_cua_hang,
        'ngay_dat': don_hang.ngay_dat.strftime('%d/%m/%Y %H:%M') if don_hang.ngay_dat else '',
        'trang_thai': don_hang.get_trang_thai_display(),
        'ghi_chu': don_hang.ghi_chu or 'Khong co',
        'tong_tien': float(don_hang.tong_tien or 0),
        'nguoi_dat': dinh_dang_ten_nguoi_dung(don_hang.nguoi_dung),
        'chi_tiets': [
            {
                'stt': i + 1,
                'ten': ct.mat_hang.ten_mat_hang,
                'so_luong': ct.so_luong,
                'don_gia': float(ct.don_gia or 0),
                'thanh_tien': float(ct.thanh_tien or 0),
            } for i, ct in enumerate(chi_tiets)
        ]
    }
    return JsonResponse(data)

