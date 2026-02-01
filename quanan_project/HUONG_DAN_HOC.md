# TÀI LIỆU HỌC DJANGO WEBGIS QUÁN ĂN

## Mục lục
1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Cấu trúc thư mục](#2-cấu-trúc-thư-mục)
3. [Models và ORM](#3-models-và-orm)
4. [Views và API](#4-views-và-api)
5. [JavaScript - map.js](#5-javascript---mapjs)
6. [JavaScript - search.js](#6-javascript---searchjs)
7. [Luồng hoạt động](#7-luồng-hoạt-động)
8. [PostGIS](#8-postgis)
9. [Cách chạy project](#9-cách-chạy-project)

---

## 1. Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                        NGƯỜI DÙNG                                │
│                    (Trình duyệt web)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   map.js     │  │  search.js   │  │  Templates   │          │
│  │  (Bản đồ)    │  │  (Tìm kiếm)  │  │  (HTML)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ fetch() / HTTP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DJANGO BACKEND                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   urls.py    │─▶│   views.py   │─▶│  models.py   │          │
│  │  (Routing)   │  │  (Xử lý)     │  │  (ORM)       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ GeoDjango ORM
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  POSTGRESQL + POSTGIS                            │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  loai_quan   │  │   quan_an    │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Cấu trúc thư mục

```
quanan_project/
├── manage.py                    # Script quản lý Django
├── quanan_project/
│   ├── settings.py              # Cấu hình (DB, Apps, GDAL)
│   └── urls.py                  # URL routing chính
└── quanan/
    ├── models.py                # ⭐ ORM Models (GeoDjango)
    ├── views.py                 # ⭐ Views + API
    ├── urls.py                  # URL routing app
    ├── static/quanan/js/
    │   ├── map.js               # ⭐ JavaScript bản đồ
    │   └── search.js            # ⭐ JavaScript tìm kiếm
    └── templates/quanan/
        ├── bando.html           # Template bản đồ
        ├── timkiem.html         # Template tìm kiếm
        ├── danh_sach.html       # Template danh sách (view tĩnh)
        ├── chi_tiet.html        # Template chi tiết (view tĩnh)
        └── thong_ke.html        # Template thống kê (view tĩnh)
```

---

## 3. Models và ORM

### 3.1. Định nghĩa Model (models.py)

```python
from django.contrib.gis.db import models  # GeoDjango

class LoaiQuan(models.Model):
    ma_loai = models.AutoField(primary_key=True)
    ten_loai = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'loai_quan'  # Tên bảng trong PostgreSQL
        managed = False          # Django không tạo/sửa bảng
    
    def __str__(self):
        return self.ten_loai


class QuanAn(models.Model):
    ma_quan = models.AutoField(primary_key=True)
    ten_quan = models.CharField(max_length=200)
    ma_loai = models.ForeignKey(LoaiQuan, on_delete=models.SET_NULL, 
                                null=True, db_column='ma_loai')
    muc_gia = models.SmallIntegerField(default=2)
    diem_danh_gia = models.DecimalField(max_digits=2, decimal_places=1)
    
    # ⭐ TRƯỜNG GEOMETRY - PostGIS
    vi_tri = models.PointField(srid=4326, null=True)
    
    class Meta:
        db_table = 'quan_an'
        managed = False
    
    # Property lấy tọa độ
    @property
    def kinh_do(self):
        return self.vi_tri.x if self.vi_tri else None
    
    @property
    def vi_do(self):
        return self.vi_tri.y if self.vi_tri else None
```

### 3.2. Các thao tác ORM thường dùng

```python
# 1. Lấy tất cả
quans = QuanAn.objects.all()

# 2. Lọc theo điều kiện
quans = QuanAn.objects.filter(ma_loai__ten_loai='Phở')

# 3. Sắp xếp
quans = QuanAn.objects.order_by('-diem_danh_gia')  # Giảm dần

# 4. Lấy 1 record
quan = QuanAn.objects.get(ma_quan=5)

# 5. Kết hợp bảng (JOIN)
quans = QuanAn.objects.select_related('ma_loai').all()

# 6. Loại trừ
quans = QuanAn.objects.exclude(ma_quan=5)

# 7. Giới hạn số lượng
quans = QuanAn.objects.all()[:10]  # Top 10

# 8. Đếm
count = QuanAn.objects.count()

# 9. Aggregate
from django.db.models import Avg, Count
avg = QuanAn.objects.aggregate(Avg('diem_danh_gia'))
```

### 3.3. GeoDjango ORM - Tìm theo vị trí

```python
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D  # Distance helper

# Tạo điểm tìm kiếm
diem_tim = Point(106.70, 10.78, srid=4326)  # (lng, lat)

# Tìm quán trong bán kính 2km
quans = QuanAn.objects.filter(
    vi_tri__distance_lte=(diem_tim, D(km=2))
)

# Tính khoảng cách và sắp xếp
quans = QuanAn.objects.annotate(
    khoang_cach=Distance('vi_tri', diem_tim)
).order_by('khoang_cach')

# Lấy khoảng cách (km)
for q in quans:
    print(q.ten_quan, q.khoang_cach.km)
```

---

## 4. Views và API

### 4.1. View tĩnh (render HTML)

```python
def danh_sach_quan(request):
    # Lấy dữ liệu từ database
    quans = QuanAn.objects.select_related('ma_loai').all()
    
    # Truyền vào template
    context = {'quans': quans}
    return render(request, 'quanan/danh_sach.html', context)
```

### 4.2. API (trả về JSON)

```python
def api_quan(request):
    quans = QuanAn.objects.select_related('ma_loai').all()
    
    # Chuyển thành list of dict
    data = [{
        'ma_quan': q.ma_quan,
        'ten_quan': q.ten_quan,
        'loai': q.ma_loai.ten_loai if q.ma_loai else None,
        'kinh_do': q.kinh_do,
        'vi_do': q.vi_do,
    } for q in quans]
    
    return JsonResponse({'status': 'success', 'data': data})
```

### 4.3. API tìm kiếm theo bán kính

```python
def api_timkiem(request):
    lat = float(request.GET.get('lat', 10.78))
    lng = float(request.GET.get('lng', 106.70))
    r = float(request.GET.get('r', 2))  # km
    
    diem_tim = Point(lng, lat, srid=4326)
    
    quans = QuanAn.objects.filter(
        vi_tri__distance_lte=(diem_tim, D(km=r))
    ).annotate(
        khoang_cach=Distance('vi_tri', diem_tim)
    ).order_by('khoang_cach')
    
    data = [{
        'ten_quan': q.ten_quan,
        'khoang_cach': round(q.khoang_cach.km, 2),
    } for q in quans]
    
    return JsonResponse({'status': 'success', 'data': data})
```

---

## 5. JavaScript - map.js

### 5.1. Biến toàn cục

```javascript
let map;                    // Đối tượng Leaflet map
let markers = {};           // Object lưu tất cả markers
let dsQuan = [];            // Mảng dữ liệu quán (đã lọc)
let dsQuanGoc = [];         // Mảng gốc (không lọc)
let loaiHT = 'all';         // Loại đang lọc
let tuKhoa = '';            // Từ khóa tìm kiếm
let circleLayer = null;     // Vòng tròn bán kính
let startMarker = null;     // Marker điểm xuất phát
let routeLayer = null;      // Đường đi
let quanDuocChon = null;    // Quán đích để chỉ đường
```

### 5.2. Khởi tạo bản đồ

```javascript
const khoiTaoMap = (elementId, lat = 10.78, lng = 106.70, zoom = 13) => {
    // Tạo map
    map = L.map(elementId).setView([lat, lng], zoom);
    
    // Thêm tile layer (nền bản đồ)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);
    
    return map;
};
```

### 5.3. Gọi API và hiển thị markers

```javascript
const loadDanhSachQuan = async () => {
    // Gọi API
    const res = await fetch('/api/quan/');
    const json = await res.json();
    
    if (json.status === 'success') {
        dsQuanGoc = json.data;
        dsQuan = json.data;
        hienThi(dsQuan);
    }
};

const hienThi = (data) => {
    // Xóa markers cũ
    Object.values(markers).forEach(m => map.removeLayer(m));
    markers = {};
    
    // Tạo markers mới
    data.forEach(quan => {
        if (quan.vi_do && quan.kinh_do) {
            const marker = L.circleMarker([quan.vi_do, quan.kinh_do], {
                radius: 8,
                fillColor: '#e74c3c',
                color: '#fff',
                weight: 2,
                fillOpacity: 0.9
            });
            
            marker.bindPopup(`<b>${quan.ten_quan}</b><br>${quan.loai}`);
            marker.addTo(map);
            markers[quan.ma_quan] = marker;
        }
    });
};
```

### 5.4. Lọc theo loại (client-side)

```javascript
const loc = () => {
    let d = dsQuanGoc;
    
    // Lọc theo loại
    if (loaiHT !== 'all') {
        d = d.filter(q => q.loai === loaiHT);
    }
    
    // Lọc theo từ khóa
    if (tuKhoa) {
        d = d.filter(q => boDau(q.ten_quan).includes(boDau(tuKhoa)));
    }
    
    return d;
};

// Bỏ dấu tiếng Việt
const boDau = s => s.normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .toLowerCase();
```

### 5.5. Lấy vị trí người dùng (GPS)

```javascript
const layViTriHienTai = () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                
                // Đặt marker
                datDiemXuatPhat(lat, lng);
                map.flyTo([lat, lng], 15);
            },
            (err) => {
                alert('Không lấy được vị trí: ' + err.message);
            }
        );
    }
};
```

### 5.6. Tìm đường với OSRM

```javascript
const timDuong = async () => {
    const startLat = parseFloat(document.getElementById('start-lat').value);
    const startLng = parseFloat(document.getElementById('start-lng').value);
    const endLat = quanDuocChon.lat;
    const endLng = quanDuocChon.lng;
    
    // Gọi OSRM API
    const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;
    
    const res = await fetch(url);
    const data = await res.json();
    
    if (data.routes && data.routes.length > 0) {
        const route = data.routes[0];
        
        // Đảo tọa độ: OSRM trả [lng, lat], Leaflet cần [lat, lng]
        const coords = route.geometry.coordinates.map(c => [c[1], c[0]]);
        
        // Vẽ đường
        if (routeLayer) map.removeLayer(routeLayer);
        routeLayer = L.polyline(coords, {
            color: '#667eea',
            weight: 5,
            opacity: 0.8
        }).addTo(map);
        
        // Hiển thị thông tin
        const distance = (route.distance / 1000).toFixed(2);
        const duration = Math.round(route.duration / 60);
        document.getElementById('route-info').innerHTML = 
            `Khoảng cách: ${distance} km<br>Thời gian: ${duration} phút`;
    }
};
```

---

## 6. JavaScript - search.js

### 6.1. Biến toàn cục

```javascript
let mapSearch;              // Bản đồ tìm kiếm
let searchMarker = null;    // Marker vị trí tìm
let searchCircle = null;    // Vòng tròn bán kính
let resultMarkers = [];     // Markers kết quả
```

### 6.2. Đặt marker và vòng tròn

```javascript
const datMarkerTimKiem = (lat, lng) => {
    if (searchMarker) mapSearch.removeLayer(searchMarker);
    
    searchMarker = L.marker([lat, lng]).addTo(mapSearch);
    searchMarker.bindPopup('Vị trí tìm kiếm').openPopup();
};

const veVongTron = (lat, lng, radiusKm) => {
    if (searchCircle) mapSearch.removeLayer(searchCircle);
    
    searchCircle = L.circle([lat, lng], {
        radius: radiusKm * 1000,  // km -> m
        color: '#667eea',
        fillOpacity: 0.1
    }).addTo(mapSearch);
};
```

### 6.3. Tìm kiếm theo vị trí

```javascript
const timKiem = async () => {
    const lat = parseFloat(document.getElementById('lat').value);
    const lng = parseFloat(document.getElementById('lng').value);
    const radius = parseFloat(document.getElementById('radius').value);
    
    // Vẽ marker và vòng tròn
    datMarkerTimKiem(lat, lng);
    veVongTron(lat, lng, radius);
    
    // Gọi API
    const res = await fetch(`/api/timkiem/?lat=${lat}&lng=${lng}&r=${radius}`);
    const json = await res.json();
    
    if (json.status === 'success') {
        hienThiKetQua(json.data);
        mapSearch.fitBounds(searchCircle.getBounds());
    }
};
```

---

## 7. Luồng hoạt động

### 7.1. Luồng load trang bản đồ

```
1. User truy cập: http://127.0.0.1:8000/
   │
   ▼
2. Django: urls.py → views.trang_chu() → render('bando.html')
   │
   ▼
3. Browser tải HTML + CSS + map.js
   │
   ▼
4. JavaScript chạy:
   ├── khoiTaoMap('map')
   ├── loadLoaiQuan() → fetch('/api/loai/')
   └── loadDanhSachQuan() → fetch('/api/quan/')
   │
   ▼
5. Hiển thị markers trên bản đồ
```

### 7.2. Luồng tìm kiếm theo bán kính

```
1. User click "Tìm kiếm"
   │
   ▼
2. JavaScript: timTheoViTri()
   └── fetch('/api/timkiem/?lat=...&lng=...&r=2')
   │
   ▼
3. Django: views.api_timkiem()
   └── ORM: QuanAn.objects.filter(vi_tri__distance_lte=...)
   │
   ▼
4. PostgreSQL + PostGIS tính toán
   │
   ▼
5. Trả về JSON → JavaScript vẽ markers
```

---

## 8. PostGIS

### 8.1. Các hàm quan trọng

| Hàm | Ý nghĩa |
|-----|---------|
| `ST_X(geom)` | Lấy kinh độ |
| `ST_Y(geom)` | Lấy vĩ độ |
| `ST_MakePoint(lng, lat)` | Tạo điểm |
| `ST_Distance(a, b)` | Tính khoảng cách |
| `ST_DWithin(a, b, r)` | Kiểm tra trong bán kính |

### 8.2. Geometry vs Geography

```sql
-- GEOMETRY: Đơn vị độ (không chính xác cho khoảng cách)
SELECT ST_Distance(a.vi_tri, b.vi_tri);

-- GEOGRAPHY: Đơn vị mét (chính xác)
SELECT ST_Distance(a.vi_tri::geography, b.vi_tri::geography);
```

---

## 9. Cách chạy project

### 9.1. Cài đặt

```bash
# 1. Cài packages
pip install django psycopg2-binary django-cors-headers

# 2. Cài OSGeo4W (cho GeoDjango trên Windows)
# Tải từ: https://trac.osgeo.org/osgeo4w/

# 3. Chạy migrations
cd d:\WebGis\quanan_project
python manage.py migrate

# 4. Tạo admin
python create_admin.py

# 5. Chạy server
python manage.py runserver 8000
```

### 9.2. Truy cập

| URL | Mô tả |
|-----|-------|
| http://127.0.0.1:8000/ | Bản đồ (JavaScript) |
| http://127.0.0.1:8000/timkiem/ | Tìm kiếm (JavaScript) |
| http://127.0.0.1:8000/danh-sach/ | Danh sách (view tĩnh) |
| http://127.0.0.1:8000/thong-ke/ | Thống kê (view tĩnh) |
| http://127.0.0.1:8000/admin/ | Trang quản trị |

---

## Tổng kết

| Công nghệ | Đã học |
|-----------|--------|
| **Django** | Models, Views, Templates, ORM |
| **GeoDjango** | PointField, Distance, D() |
| **PostgreSQL** | PostGIS, geometry, geography |
| **JavaScript** | fetch, async/await, Leaflet |
| **Leaflet.js** | Map, Marker, Circle, Polyline |
| **OSRM** | Routing API |
