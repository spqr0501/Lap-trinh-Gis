"""
Cong Cu GIS Tu Viet - Khong Su Dung Thu Vien Ben Ngoai
Custom GIS Tools - Implemented without external libraries
"""

import math


class CongCuGIS:
    """
    Bo cong cu GIS tu viet
    Collection of custom GIS utility functions
    """
    
    # Ban kinh trai dat theo kilometers
    BAN_KINH_TRAI_DAT_KM = 6371.0
    
    @staticmethod
    def tinh_khoang_cach_haversine(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2):
        """
        Tinh khoang cach giua 2 diem tren trai dat bang cong thuc Haversine
        
        GIAI THICH:
        - Cong thuc Haversine duoc su dung de tinh khoang cach giua 2 diem
          tren mat cau (trai dat) dua vao toa do kinh vi do
        - Do chinh xac cao cho cac khoang cach < 1000km
        - San so cua tinh toan so voi WGS84 ellipsoid < 0.5%
        
        THAM SO:
            vi_do_1, kinh_do_1: Toa do diem thu nhat (do)
            vi_do_2, kinh_do_2: Toa do diem thu hai (do)
        
        TRA VE:
            Khoang cach theo don vi kilometers
            
        VI DU:
            >>> khoang_cach = tinh_khoang_cach_haversine(16.05, 108.20, 16.06, 108.21)
            >>> print(f"{khoang_cach:.2f} km")
        """
        # Chuyen doi tu do sang radian
        vi_do_1_rad = math.radians(vi_do_1)
        kinh_do_1_rad = math.radians(kinh_do_1)
        vi_do_2_rad = math.radians(vi_do_2)
        kinh_do_2_rad = math.radians(kinh_do_2)
        
        # Cong thuc Haversine
        chenh_lech_vi_do = vi_do_2_rad - vi_do_1_rad
        chenh_lech_kinh_do = kinh_do_2_rad - kinh_do_1_rad
        
        a = math.sin(chenh_lech_vi_do/2)**2 + \
            math.cos(vi_do_1_rad) * math.cos(vi_do_2_rad) * math.sin(chenh_lech_kinh_do/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        khoang_cach = CongCuGIS.BAN_KINH_TRAI_DAT_KM * c
        return khoang_cach
    
    @staticmethod
    def tim_diem_gan_nhat(vi_do_goc, kinh_do_goc, danh_sach_diem):
        """
        Tim diem gan nhat tu mot danh sach cac diem
        
        GIAI THICH:
        - Duyet qua tat ca cac diem trong danh sach
        - Tinh khoang cach tu diem goc den tung diem
        - Luu lai diem co khoang cach nho nhat
        - Do phuc tap: O(n) voi n la so luong diem
        
        THAM SO:
            vi_do_goc, kinh_do_goc: Toa do diem goc
            danh_sach_diem: Danh sach cac tuple [(vi_do, kinh_do, du_lieu), ...]
        
        TRA VE:
            Tuple cua (diem_gan_nhat, khoang_cach) hoac (None, None) neu khong co diem
            
        VI DU:
            >>> diem = [(16.05, 108.20, "CuaHang A"), (16.10, 108.25, "CuaHang B")]
            >>> gan_nhat, kc = tim_diem_gan_nhat(16.055, 108.205, diem)
            >>> print(f"Gan nhat: {gan_nhat[2]}, cach {kc:.2f} km")
        """
        if not danh_sach_diem:
            return None, None
        
        khoang_cach_nho_nhat = float('inf')
        diem_gan_nhat = None
        
        for diem in danh_sach_diem:
            vi_do, kinh_do = diem[0], diem[1]
            khoang_cach = CongCuGIS.tinh_khoang_cach_haversine(
                vi_do_goc, kinh_do_goc, vi_do, kinh_do
            )
            
            if khoang_cach < khoang_cach_nho_nhat:
                khoang_cach_nho_nhat = khoang_cach
                diem_gan_nhat = diem
        
        return diem_gan_nhat, khoang_cach_nho_nhat
    
    @staticmethod
    def kiem_tra_diem_trong_da_giac(vi_do_diem, kinh_do_diem, toa_do_da_giac):
        """
        Kiem tra xem mot diem co nam trong da giac (polygon) khong
        
        GIAI THICH:
        - Su dung thuat toan Ray Casting (ban tia):
          + Ve mot tia tu diem ra vo cuc
          + Dem so lan tia cat cac canh cua da giac
          + Neu so lan cat la le => diem nam trong
          + Neu so lan cat la chan => diem nam ngoai
        - Do phuc tap: O(m) voi m la so canh cua da giac
        - Hoat dong voi polygon loi (concave) va polygon lom (convex)
        
        THAM SO:
            vi_do_diem, kinh_do_diem: Toa do diem can kiem tra
            toa_do_da_giac: Danh sach cac tuple (vi_do, kinh_do) tao thanh da giac
        
        TRA VE:
            True neu diem nam trong da giac, False neu nam ngoai
            
        VI DU:
            >>> khu_vuc = [(16.00, 108.00), (16.00, 108.50), 
            ...            (16.50, 108.50), (16.50, 108.00)]
            >>> trong_khu_vuc = kiem_tra_diem_trong_da_giac(16.25, 108.25, khu_vuc)
            >>> print(f"Diem trong khu vuc: {trong_khu_vuc}")
        """
        x, y = kinh_do_diem, vi_do_diem
        so_luong_dinh = len(toa_do_da_giac)
        nam_trong = False
        
        diem1_x, diem1_y = toa_do_da_giac[0][1], toa_do_da_giac[0][0]  # kinh_do, vi_do
        
        for i in range(so_luong_dinh + 1):
            diem2_x, diem2_y = toa_do_da_giac[i % so_luong_dinh][1], \
                               toa_do_da_giac[i % so_luong_dinh][0]
            
            # Thuat toan ray casting
            if y > min(diem1_y, diem2_y):
                if y <= max(diem1_y, diem2_y):
                    if x <= max(diem1_x, diem2_x):
                        if diem1_y != diem2_y:
                            giao_diem_x = (y - diem1_y) * (diem2_x - diem1_x) / (diem2_y - diem1_y) + diem1_x
                        if diem1_x == diem2_x or x <= giao_diem_x:
                            nam_trong = not nam_trong
            
            diem1_x, diem1_y = diem2_x, diem2_y
        
        return nam_trong
    
    @staticmethod
    def tinh_dien_tich_da_giac(toa_do_da_giac):
        """
        Tinh dien tich cua da giac bang cong thuc Shoelace
        
        GIAI THICH:
        - Cong thuc Shoelace (day giay):
          + Nhan cheo cac toa do theo chieu kim dong ho
          + Tru di nhan cheo nguoc chieu
          + Chia 2 va lay tri tuyet doi
        - Ket qua la xap xi cho da giac nho (< 100 km²)
        - Gia dinh mat phang 2D (du trai dat la hinh cau)
        
        THAM SO:
            toa_do_da_giac: Danh sach cac tuple (vi_do, kinh_do)
        
        TRA VE:
            Dien tich tinh bang kilometer vuong (xap xi)
            
        VI DU:
            >>> da_giac = [(16.05, 108.20), (16.06, 108.20), 
            ...            (16.06, 108.21), (16.05, 108.21)]
            >>> dien_tich = tinh_dien_tich_da_giac(da_giac)
            >>> print(f"Dien tich: {dien_tich:.2f} km²")
        """
        if len(toa_do_da_giac) < 3:
            return 0
        
        # Cong thuc Shoelace
        dien_tich = 0
        so_dinh = len(toa_do_da_giac)
        
        for i in range(so_dinh):
            j = (i + 1) % so_dinh
            dien_tich += toa_do_da_giac[i][1] * toa_do_da_giac[j][0]
            dien_tich -= toa_do_da_giac[j][1] * toa_do_da_giac[i][0]
        
        dien_tich = abs(dien_tich) / 2.0
        
        # Chuyen doi sang km² (xap xi: 1 do ≈ 111 km o xuyen dao)
        dien_tich_km2 = dien_tich * (111.0 ** 2)
        
        return dien_tich_km2
    
    @staticmethod
    def tao_vung_dem_hinh_tron(vi_do_tam, kinh_do_tam, ban_kinh_km, so_diem=32):
        """
        Tao vung dem (buffer) hinh tron xung quanh mot diem
        
        GIAI THICH:
        - Tao N diem deu nhau tren duong tron
        - Su dung cong thuc luong giac de tinh toa do moi diem:
          + Goc = 2π * i / N (voi i tu 0 den N-1)
          + Delta latitude = ban_kinh * cos(goc)
          + Delta longitude = ban_kinh * sin(goc) / cos(latitude)
        - Ket qua la xap xi hinh tron (da giac N canh)
        
        THAM SO:
            vi_do_tam, kinh_do_tam: Toa do tam duong tron
            ban_kinh_km: Ban kinh theo kilometers
            so_diem: So diem tao thanh duong tron (mac dinh 32)
        
        TRA VE:
            Danh sach cac tuple (vi_do, kinh_do) tao thanh duong tron
            
        VI DU:
            >>> vung_dem = tao_vung_dem_hinh_tron(16.05, 108.20, 5.0, so_diem=16)
            >>> print(f"Vung dem co {len(vung_dem)} diem")
        """
        danh_sach_diem_tron = []
        
        for i in range(so_diem):
            # Goc theo radian
            goc = 2 * math.pi * i / so_diem
            
            # Tinh do chenh lech theo km
            delta_vi_do = ban_kinh_km / CongCuGIS.BAN_KINH_TRAI_DAT_KM * math.cos(goc)
            delta_kinh_do = ban_kinh_km / (CongCuGIS.BAN_KINH_TRAI_DAT_KM * 
                                           math.cos(math.radians(vi_do_tam))) * math.sin(goc)
            
            # Chuyen doi sang do
            vi_do_moi = vi_do_tam + math.degrees(delta_vi_do)
            kinh_do_moi = kinh_do_tam + math.degrees(delta_kinh_do)
            
            danh_sach_diem_tron.append((vi_do_moi, kinh_do_moi))
        
        return danh_sach_diem_tron
    
    @staticmethod
    def tinh_diem_trung_tam(danh_sach_diem):
        """
        Tinh diem trung tam (centroid) cua nhieu diem
        
        GIAI THICH:
        - Tinh trung binh cong cac toa do
        - Don gian nhung hieu qua cho phan lon truong hop
        - Khong phai la centroid hinh hoc chinh xac cho da giac phuc tap
        
        THAM SO:
            danh_sach_diem: Danh sach cac tuple (vi_do, kinh_do)
        
        TRA VE:
            Tuple cua (vi_do_trung_tam, kinh_do_trung_tam)
            
        VI DU:
            >>> diem = [(16.05, 108.20), (16.06, 108.21), (16.04, 108.19)]
            >>> tam = tinh_diem_trung_tam(diem)
            >>> print(f"Diem trung tam: {tam}")
        """
        if not danh_sach_diem:
            return None, None
        
        tong_vi_do = sum(diem[0] for diem in danh_sach_diem)
        tong_kinh_do = sum(diem[1] for diem in danh_sach_diem)
        
        vi_do_trung_tam = tong_vi_do / len(danh_sach_diem)
        kinh_do_trung_tam = tong_kinh_do / len(danh_sach_diem)
        
        return vi_do_trung_tam, kinh_do_trung_tam
    
    @staticmethod
    def tinh_huong_di(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2):
        """
        Tinh huong di (bearing/azimuth) tu diem 1 den diem 2
        
        GIAI THICH:
        - Bearing la goc giua huong Bac va duong di, do theo chieu kim dong ho
        - Ket qua: 0° = Bac, 90° = Dong, 180° = Nam, 270° = Tay
        - Su dung ham atan2 de tinh goc chinh xac
        - Co the chuyen doi thanh 8 huong chinh: Bac, Dong Bac, Dong, etc.
        
        THAM SO:
            vi_do_1, kinh_do_1: Toa do diem xuat phat
            vi_do_2, kinh_do_2: Toa do diem dich den
        
        TRA VE:
            Goc bearing theo don vi do (0-360°)
            
        VI DU:
            >>> huong = tinh_huong_di(16.05, 108.20, 16.06, 108.21)
            >>> print(f"Huong di: {huong:.1f}° (Dong Bac)")
        """
        vi_do_1_rad = math.radians(vi_do_1)
        vi_do_2_rad = math.radians(vi_do_2)
        chenh_lech_kinh_do_rad = math.radians(kinh_do_2 - kinh_do_1)
        
        x = math.sin(chenh_lech_kinh_do_rad) * math.cos(vi_do_2_rad)
        y = math.cos(vi_do_1_rad) * math.sin(vi_do_2_rad) - \
            math.sin(vi_do_1_rad) * math.cos(vi_do_2_rad) * math.cos(chenh_lech_kinh_do_rad)
        
        huong_rad = math.atan2(x, y)
        huong_do = math.degrees(huong_rad)
        
        # Chuan hoa ve 0-360°
        huong_do = (huong_do + 360) % 360
        
        return huong_do
    
    @staticmethod
    def lay_khung_bao(danh_sach_diem, khoang_dem_km=0):
        """
        Lay khung bao (bounding box) cho mot tap hop cac diem
        
        GIAI THICH:
        - Tim toa do nho nhat va lon nhat (min/max) cua tat ca cac diem
        - Tao hinh chu nhat bao quanh tat ca cac diem
        - Co the them khoang dem (padding) de mo rong khung bao
        - Huu ich khi fit map bounds de hien thi tat ca cac diem
        
        THAM SO:
            danh_sach_diem: Danh sach cac tuple (vi_do, kinh_do)
            khoang_dem_km: Khoang dem them theo kilometers
        
        TRA VE:
            Tuple cua ((vi_do_min, kinh_do_min), (vi_do_max, kinh_do_max))
            
        VI DU:
            >>> diem = [(16.05, 108.20), (16.10, 108.25)]
            >>> khung = lay_khung_bao(diem, khoang_dem_km=1)
            >>> print(f"Khung bao: {khung}")
        """
        if not danh_sach_diem:
            return None
        
        cac_vi_do = [p[0] for p in danh_sach_diem]
        cac_kinh_do = [p[1] for p in danh_sach_diem]
        
        vi_do_min = min(cac_vi_do)
        vi_do_max = max(cac_vi_do)
        kinh_do_min = min(cac_kinh_do)
        kinh_do_max = max(cac_kinh_do)
        
        # Them khoang dem
        if khoang_dem_km > 0:
            dem_vi_do = khoang_dem_km / CongCuGIS.BAN_KINH_TRAI_DAT_KM * (180 / math.pi)
            vi_do_trung_binh = (vi_do_min + vi_do_max) / 2
            dem_kinh_do = khoang_dem_km / (CongCuGIS.BAN_KINH_TRAI_DAT_KM * 
                                           math.cos(math.radians(vi_do_trung_binh))) * (180 / math.pi)
            
            vi_do_min -= dem_vi_do
            vi_do_max += dem_vi_do
            kinh_do_min -= dem_kinh_do
            kinh_do_max += dem_kinh_do
        
        return (vi_do_min, kinh_do_min), (vi_do_max, kinh_do_max)
    
    @staticmethod
    def tim_diem_trong_ban_kinh(vi_do_goc, kinh_do_goc, danh_sach_diem, ban_kinh_km):
        """
        Tim tat ca cac diem nam trong ban kinh cho truoc
        
        GIAI THICH:
        - Duyet qua tung diem trong danh sach
        - Tinh khoang cach tu diem goc den tung diem
        - Chi giu lai cac diem co khoang cach <= ban kinh
        - Sap xep ket qua theo khoang cach (gan nhat truoc)
        - Do phuc tap: O(n log n) voi n la so diem (do sorting)
        
        THAM SO:
            vi_do_goc, kinh_do_goc: Toa do diem goc
            danh_sach_diem: Danh sach cac tuple (vi_do, kinh_do, du_lieu)
            ban_kinh_km: Ban kinh tim kiem theo kilometers
        
        TRA VE:
            Danh sach cac dict {'diem': ..., 'khoang_cach': ...} da sap xep
            
        VI DU:
            >>> diem = [(16.05, 108.20, "A"), (16.10, 108.25, "B")]
            >>> ket_qua = tim_diem_trong_ban_kinh(16.05, 108.20, diem, 10.0)
            >>> for kq in ket_qua:
            ...     print(f"{kq['diem'][2]}: {kq['khoang_cach']:.2f} km")
        """
        ket_qua = []
        
        for diem in danh_sach_diem:
            vi_do, kinh_do = diem[0], diem[1]
            khoang_cach = CongCuGIS.tinh_khoang_cach_haversine(
                vi_do_goc, kinh_do_goc, vi_do, kinh_do
            )
            
            if khoang_cach <= ban_kinh_km:
                ket_qua.append({
                    'diem': diem,
                    'khoang_cach': khoang_cach
                })
        
        # Sap xep theo khoang cach
        ket_qua.sort(key=lambda x: x['khoang_cach'])
        
        return ket_qua
    
    @staticmethod
    def don_gian_hoa_duong(danh_sach_diem, do_chiu_sai_so=0.0001):
        """
        Don gian hoa duong di bang thuat toan Douglas-Peucker
        
        GIAI THICH:
        - Thuat toan Douglas-Peucker giam so diem trong duong di
          ma van giu nguyen hinh dang tong the:
          1. Noi diem dau va diem cuoi
          2. Tim diem co khoang cach vuong goc lon nhat den duong noi
          3. Neu khoang cach > nguong => giu diem do, de quy 2 doan
          4. Neu khoang cach <= nguong => loai bo tat ca diem giua
        - Do phuc tap: O(n log n) best case, O(n²) worst case
        - Huu ich de giam dung luong du lieu route tu GPS
        
        THAM SO:
            danh_sach_diem: Danh sach cac tuple (vi_do, kinh_do)
            do_chiu_sai_so: Nguong sai so cho phep (cang lon cang don gian)
        
        TRA VE:
            Danh sach diem da duoc don gian hoa
            
        VI DU:
            >>> route = [(16.05, 108.20), (16.051, 108.201), ..., (16.06, 108.25)]
            >>> route_gian = don_gian_hoa_duong(route, do_chiu_sai_so=0.001)
            >>> print(f"Giam tu {len(route)} xuong {len(route_gian)} diem")
        """
        if len(danh_sach_diem) < 3:
            return danh_sach_diem
        
        def tinh_khoang_cach_vuong_goc(diem, diem_dau_duong, diem_cuoi_duong):
            """Tinh khoang cach vuong goc tu diem den duong thang"""
            x0, y0 = diem[1], diem[0]  # kinh_do, vi_do
            x1, y1 = diem_dau_duong[1], diem_dau_duong[0]
            x2, y2 = diem_cuoi_duong[1], diem_cuoi_duong[0]
            
            tu_so = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
            mau_so = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
            
            if mau_so == 0:
                return 0
            
            return tu_so / mau_so
        
        def thuat_toan_douglas_peucker(diem_list, sai_so):
            """Thuat toan Douglas-Peucker (de quy)"""
            if len(diem_list) < 3:
                return diem_list
            
            # Tim diem co khoang cach lon nhat
            khoang_cach_max = 0
            chi_so_max = 0
            
            for i in range(1, len(diem_list) - 1):
                khoang_cach = tinh_khoang_cach_vuong_goc(
                    diem_list[i], diem_list[0], diem_list[-1]
                )
                if khoang_cach > khoang_cach_max:
                    khoang_cach_max = khoang_cach
                    chi_so_max = i
            
            # Neu khoang cach lon hon sai so, de quy don gian hoa
            if khoang_cach_max > sai_so:
                phan_trai = thuat_toan_douglas_peucker(diem_list[:chi_so_max + 1], sai_so)
                phan_phai = thuat_toan_douglas_peucker(diem_list[chi_so_max:], sai_so)
                
                # Ket hop ket qua
                return phan_trai[:-1] + phan_phai
            else:
                return [diem_list[0], diem_list[-1]]
        
        return thuat_toan_douglas_peucker(danh_sach_diem, do_chiu_sai_so)


# Cac ham tien ich de su dung nhanh (convenience functions)
def khoang_cach_km(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2):
    """Tinh khoang cach bang kilometers"""
    return CongCuGIS.tinh_khoang_cach_haversine(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2)


def khoang_cach_met(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2):
    """Tinh khoang cach bang meters"""
    return CongCuGIS.tinh_khoang_cach_haversine(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2) * 1000


def kiem_tra_diem_trong(vi_do, kinh_do, da_giac):
    """Kiem tra diem co nam trong da giac khong"""
    return CongCuGIS.kiem_tra_diem_trong_da_giac(vi_do, kinh_do, da_giac)


def tim_gan_nhat(vi_do_goc, kinh_do_goc, danh_sach_diem):
    """Tim diem gan nhat tu danh sach"""
    return CongCuGIS.tim_diem_gan_nhat(vi_do_goc, kinh_do_goc, danh_sach_diem)
