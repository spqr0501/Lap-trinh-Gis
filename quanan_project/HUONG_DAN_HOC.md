# TÀI LIỆU HỌC DJANGO WEBGIS QUÁN ĂN

## Mục lục
1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Cấu trúc thư mục](#2-cấu-trúc-thư-mục)
3. [Luồng hoạt động](#3-luồng-hoạt-động)
4. [Chi tiết code từng file](#4-chi-tiết-code-từng-file)
5. [PostGIS và các hàm không gian](#5-postgis-và-các-hàm-không-gian)
6. [Frontend - JavaScript quan trọng](#6-frontend---javascript-quan-trọng)
7. [API Endpoints](#7-api-endpoints)
8. [Cách chạy project](#8-cách-chạy-project)

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
│                     FRONTEND (HTML/CSS/JS)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Leaflet.js  │  │   Sidebar    │  │  API Calls   │          │
│  │  (Bản đồ)    │  │  (Danh sách) │  │  (fetch)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP Request
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DJANGO BACKEND                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   urls.py    │─▶│   views.py   │─▶│   models.py  │          │
│  │  (Routing)   │  │  (Xử lý)     │  │  (Dữ liệu)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ SQL Query
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  POSTGRESQL + POSTGIS                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  loai_quan   │  │   quan_an    │  │ dac_trung_   │          │
│  │  (Loại)      │  │  (Quán ăn)   │  │ quan         │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Cấu trúc thư mục

```
d:\WebGis\quanan_project\
├── manage.py                    # Script quản lý Django
├── create_admin.py              # Script tạo admin
├── quanan_project/              # Package cấu hình
│   ├── settings.py              # ⭐ Cấu hình Django
│   └── urls.py                  # URL routing chính
└── quanan/                      # ⭐ App chính
    ├── models.py                # ⭐ Định nghĩa model
    ├── views.py                 # ⭐ Xử lý API
    ├── urls.py                  # URL routing app
    ├── admin.py                 # Cấu hình admin
    └── templates/quanan/
        └── bando.html           # ⭐ Template bản đồ
```

---

## 3. Luồng hoạt động

### Khi người dùng truy cập trang web:

```
1. User truy cập: http://127.0.0.1:8000/
        ↓
2. Django nhận request → urls.py tìm pattern
        ↓
3. views.trang_chu() render template bando.html
        ↓
4. Browser tải HTML → chạy JavaScript
        ↓
5. Leaflet.js tạo bản đồ
        ↓
6. fetch() gọi /api/quan/ lấy dữ liệu
        ↓
7. Hiển thị markers trên bản đồ
```

---

## 4. Chi tiết code từng file

### 4.1. settings.py - Cấu hình Django

**📍 File: `quanan_project/settings.py`**

```python
# ============================================================
# CẤU HÌNH DATABASE (PostgreSQL + PostGIS)
# ============================================================
# Đây là phần quan trọng nhất - kết nối Django với PostGIS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Driver PostgreSQL
        'NAME': 'quan_an',       # Tên database (phải tạo trước trong PostgreSQL)
        'USER': 'postgres',      # Username PostgreSQL
        'PASSWORD': '123456',    # Password PostgreSQL
        'HOST': 'localhost',     # Host (máy local)
        'PORT': '5432',          # Port mặc định PostgreSQL
    }
}
```

**💡 Giải thích:**
- `ENGINE`: Django dùng driver `psycopg2` để kết nối PostgreSQL
- `NAME`: Tên database đã tạo chứa các bảng quan_an, loai_quan
- Database này đã được tạo từ Notebook với PostGIS extension

```python
# ============================================================
# CÁC ỨNG DỤNG (APPS)
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',     # Trang admin quản trị
    'django.contrib.auth',      # Xác thực user (login/logout)
    'corsheaders',              # Cho phép Cross-Origin requests
    'quanan',                   # App của chúng ta!
]
```

**💡 Giải thích:**
- `corsheaders`: Cho phép frontend gọi API từ domain khác (cần cho development)
- `quanan`: App chính chứa models, views, templates

---

### 4.2. models.py - Định nghĩa Model

**📍 File: `quanan/models.py`**

```python
class LoaiQuan(models.Model):
    """
    Model ánh xạ với bảng loai_quan trong PostgreSQL.
    Lưu các loại quán: Phở, Bún, Cơm, Lẩu, Gà, Cafe...
    """
    ma_loai = models.AutoField(primary_key=True)  # Khóa chính tự tăng
    ten_loai = models.CharField(max_length=100)   # Tên loại
    
    class Meta:
        db_table = 'loai_quan'  # ⭐ Tên bảng THẬT trong database
        managed = False         # ⭐ Django KHÔNG tạo/sửa/xóa bảng này
    
    def __str__(self):
        return self.ten_loai  # Hiển thị tên trong Admin
```

**💡 Giải thích `managed = False`:**
- Bảng `loai_quan` đã tồn tại trong database (tạo bởi Notebook)
- Django chỉ ĐỌC/GHI dữ liệu, không quản lý schema
- Nếu `managed = True`: Django sẽ tạo bảng mới (không muốn!)

```python
class QuanAn(models.Model):
    """
    Model ánh xạ với bảng quan_an.
    """
    ma_quan = models.AutoField(primary_key=True)
    ten_quan = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True, null=True)
    
    # ⭐ Foreign Key - liên kết với bảng loai_quan
    ma_loai = models.ForeignKey(
        LoaiQuan,                    # Model tham chiếu
        on_delete=models.SET_NULL,   # Nếu xóa loại → set null
        null=True,
        db_column='ma_loai'          # Tên cột trong database
    )
    
    muc_gia = models.SmallIntegerField(default=2)  # 1-5 ($-$$$$$)
    diem_danh_gia = models.DecimalField(max_digits=2, decimal_places=1)
    
    class Meta:
        db_table = 'quan_an'
        managed = False
```

**💡 Tại sao không có trường `vi_tri`?**
- `vi_tri` là geometry POINT (kiểu dữ liệu PostGIS)
- Django thuần không hỗ trợ geometry
- Ta dùng **raw SQL** với `ST_X()`, `ST_Y()` để lấy tọa độ

---

### 4.3. views.py - Xử lý API (QUAN TRỌNG NHẤT!)

**📍 File: `quanan/views.py`**

#### API 1: Lấy danh sách quán ăn

```python
def api_quan(request):
    """
    API: Lấy danh sách tất cả quán ăn với tọa độ.
    URL: GET /api/quan/
    """
    
    # ⭐ SQL Query với PostGIS functions
    sql = """
    SELECT q.ma_quan, q.ten_quan, l.ten_loai, q.muc_gia, 
           q.diem_danh_gia, q.so_luot_danh_gia, q.dia_chi,
           ST_X(q.vi_tri),   -- ⭐ Lấy KINH ĐỘ từ geometry
           ST_Y(q.vi_tri)    -- ⭐ Lấy VĨ ĐỘ từ geometry
    FROM quan_an q 
    LEFT JOIN loai_quan l ON q.ma_loai = l.ma_loai
    ORDER BY q.diem_danh_gia DESC
    """
    
    # ⭐ Thực thi SQL trực tiếp (không qua ORM)
    with connection.cursor() as c:
        c.execute(sql)
        
        # Chuyển kết quả thành list of dict
        data = [{
            'ma_quan': r[0], 
            'ten_quan': r[1], 
            'loai': r[2],
            'muc_gia': r[3], 
            'diem': float(r[4] or 0),  # Decimal → float
            'kinh_do': float(r[7] or 0), 
            'vi_do': float(r[8] or 0)
        } for r in c.fetchall()]
    
    # ⭐ Trả về JSON
    return JsonResponse({'status': 'success', 'data': data})
```

**💡 Giải thích:**
- `ST_X(vi_tri)`: Hàm PostGIS trích xuất kinh độ (longitude)
- `ST_Y(vi_tri)`: Hàm PostGIS trích xuất vĩ độ (latitude)
- `connection.cursor()`: Kết nối trực tiếp database để chạy raw SQL
- `JsonResponse`: Trả về JSON cho frontend

---

#### API 2: Tìm quán theo vị trí + bán kính (GIS CORE!)

```python
def api_timkiem(request):
    """
    API: Tìm quán ăn trong bán kính từ 1 điểm.
    URL: GET /api/timkiem/?lat=10.78&lng=106.70&r=2
    """
    
    # ⭐ Lấy params từ URL query string
    lat = float(request.GET.get('lat', 10.78))   # Vĩ độ
    lng = float(request.GET.get('lng', 106.70))  # Kinh độ
    r = float(request.GET.get('r', 2)) * 1000    # Bán kính: km → mét
    
    # ⭐ SQL với PostGIS spatial functions
    sql = f"""
    SELECT q.ma_quan, q.ten_quan, l.ten_loai, q.muc_gia, q.diem_danh_gia,
           ST_X(q.vi_tri), ST_Y(q.vi_tri),
           
           -- ⭐ Tính khoảng cách từ điểm tìm kiếm đến quán
           ST_Distance(
               q.vi_tri::geography,  -- Chuyển sang geography (đơn vị mét)
               ST_SetSRID(ST_MakePoint({lng},{lat}), 4326)::geography
           ) / 1000 as khoang_cach_km
           
    FROM quan_an q 
    LEFT JOIN loai_quan l ON q.ma_loai = l.ma_loai
    
    -- ⭐ Điều kiện: quán nằm trong bán kính r mét
    WHERE ST_DWithin(
        q.vi_tri::geography,
        ST_SetSRID(ST_MakePoint({lng},{lat}), 4326)::geography,
        {r}  -- Bán kính tính bằng mét
    )
    ORDER BY 8  -- Sắp xếp theo khoảng cách
    """
    
    with connection.cursor() as c:
        c.execute(sql)
        data = [{
            'ma_quan': r[0], 
            'ten_quan': r[1], 
            'loai': r[2],
            'khoang_cach': round(float(r[7] or 0), 2)  # Làm tròn 2 số
        } for r in c.fetchall()]
    
    return JsonResponse({'status': 'success', 'data': data})
```

**💡 Giải thích từng hàm PostGIS:**

| Hàm | Ý nghĩa |
|-----|---------|
| `ST_MakePoint(lng, lat)` | Tạo POINT geometry từ tọa độ |
| `ST_SetSRID(..., 4326)` | Đặt hệ tọa độ WGS84 (GPS) |
| `::geography` | Chuyển sang geography để tính bằng MÉT |
| `ST_Distance(a, b)` | Tính khoảng cách giữa 2 điểm |
| `ST_DWithin(a, b, r)` | Kiểm tra a có trong bán kính r của b |

---

#### API 3: Gợi ý quán tương tự

```python
def api_goiy(request, ma_quan):
    """
    API: Gợi ý quán CÙNG LOẠI với quán được chọn.
    URL: GET /api/goiy/1/  (ma_quan = 1)
    """
    
    # Lấy số lượng gợi ý từ query param
    top = int(request.GET.get('top', 5))
    
    # ⭐ Bước 1: Lấy loại của quán hiện tại
    with connection.cursor() as c:
        c.execute("SELECT ma_loai FROM quan_an WHERE ma_quan = %s", [ma_quan])
        row = c.fetchone()
    
    if not row:
        return JsonResponse({'status': 'error', 'data': []})
    
    ma_loai = row[0]
    
    # ⭐ Bước 2: Tìm quán CÙNG LOẠI, trừ quán hiện tại
    sql = """
    SELECT q.ma_quan, q.ten_quan, l.ten_loai, q.diem_danh_gia,
           ST_X(q.vi_tri), ST_Y(q.vi_tri)
    FROM quan_an q 
    LEFT JOIN loai_quan l ON q.ma_loai = l.ma_loai
    WHERE q.ma_quan != %s     -- Loại trừ quán hiện tại
      AND q.ma_loai = %s      -- Cùng loại
    ORDER BY q.diem_danh_gia DESC  -- Sắp xếp theo điểm
    LIMIT %s
    """
    
    with connection.cursor() as c:
        c.execute(sql, [ma_quan, ma_loai, top])
        data = [...]
    
    return JsonResponse({'status': 'success', 'data': data})
```

---

### 4.4. urls.py - URL Routing

**📍 File: `quanan/urls.py`**

```python
from django.urls import path
from . import views

urlpatterns = [
    # Trang chính - render template bando.html
    path('', views.trang_chu),
    
    # ⭐ API endpoints
    path('api/loai/', views.api_loai),      # GET /api/loai/
    path('api/quan/', views.api_quan),      # GET /api/quan/
    path('api/timkiem/', views.api_timkiem),# GET /api/timkiem/?lat=...&lng=...&r=...
    
    # ⭐ URL với parameter
    path('api/goiy/<int:ma_quan>/', views.api_goiy),
    # <int:ma_quan> = lấy số nguyên từ URL
    # VD: /api/goiy/1/ → ma_quan = 1
]
```

---

## 5. PostGIS và các hàm không gian

### 5.1. Hệ tọa độ (SRID)

| SRID | Tên | Đơn vị | Sử dụng |
|------|-----|--------|---------|
| 4326 | WGS84 | Độ | GPS, Google Maps |
| 3857 | Web Mercator | Mét | Tile maps |

### 5.2. Geometry vs Geography

```sql
-- GEOMETRY: Tính trên mặt phẳng (nhanh nhưng không chính xác)
SELECT ST_Distance(a.vi_tri, b.vi_tri);  -- Đơn vị: độ

-- GEOGRAPHY: Tính trên quả cầu (chính xác, đơn vị mét)
SELECT ST_Distance(a.vi_tri::geography, b.vi_tri::geography);  -- Đơn vị: mét
```

### 5.3. Các hàm thường dùng

```sql
-- 1. Lấy tọa độ từ POINT
SELECT ST_X(vi_tri) as kinh_do, ST_Y(vi_tri) as vi_do FROM quan_an;

-- 2. Tạo POINT từ tọa độ
SELECT ST_SetSRID(ST_MakePoint(106.70, 10.78), 4326);

-- 3. Tính khoảng cách (mét)
SELECT ST_Distance(
    a.vi_tri::geography,
    b.vi_tri::geography
) as khoang_cach_met;

-- 4. Tìm quán trong bán kính 2km
SELECT * FROM quan_an q
WHERE ST_DWithin(
    q.vi_tri::geography,
    ST_SetSRID(ST_MakePoint(106.70, 10.78), 4326)::geography,
    2000  -- 2000 mét = 2km
);
```

---

## 6. Frontend - JavaScript quan trọng

**📍 File: `templates/quanan/bando.html`**

### 6.1. Khởi tạo Leaflet Map

```javascript
// ⭐ Tạo bản đồ, tâm tại TP.HCM, zoom level 13
const map = L.map('map').setView([10.78, 106.70], 13);

// ⭐ Thêm tile layer từ OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
    .addTo(map);
```

**💡 Giải thích:**
- `L.map('map')`: Tạo map trong element có id="map"
- `setView([lat, lng], zoom)`: Đặt tâm và mức zoom
- Tile layer: Ảnh nền bản đồ từ OpenStreetMap

---

### 6.2. Gọi API và hiển thị markers

```javascript
// ⭐ Gọi API lấy danh sách quán
fetch('/api/quan/')
    .then(response => response.json())
    .then(json => {
        
        // Duyệt từng quán
        json.data.forEach(quan => {
            
            // ⭐ Tạo circle marker
            const marker = L.circleMarker([quan.vi_do, quan.kinh_do], {
                radius: 8,           // Bán kính điểm
                fillColor: '#e74c3c', // Màu nền
                color: '#fff',       // Màu viền
                weight: 2,           // Độ dày viền
                fillOpacity: 0.9     // Độ trong suốt
            });
            
            // ⭐ Gắn popup (click để hiện)
            marker.bindPopup(`
                <b>${quan.ten_quan}</b><br>
                ${quan.loai} | ⭐ ${quan.diem}
            `);
            
            // Thêm vào map
            marker.addTo(map);
        });
    });
```

---

### 6.3. Lấy vị trí người dùng (Geolocation)

```javascript
const layViTriHienTai = () => {
    // ⭐ Kiểm tra trình duyệt có hỗ trợ không
    if (navigator.geolocation) {
        
        navigator.geolocation.getCurrentPosition(
            // ⭐ Callback khi thành công
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                // Đặt marker tại vị trí người dùng
                L.marker([lat, lng]).addTo(map)
                    .bindPopup('Vị trí của bạn')
                    .openPopup();
                
                // Di chuyển map đến vị trí
                map.flyTo([lat, lng], 15);
            },
            
            // ⭐ Callback khi lỗi
            (error) => {
                alert('Không lấy được vị trí: ' + error.message);
            },
            
            // ⭐ Options
            { 
                enableHighAccuracy: true,  // Độ chính xác cao
                timeout: 10000             // Timeout 10 giây
            }
        );
    }
};
```

---

### 6.4. Tìm đường với OSRM

```javascript
const timDuong = async () => {
    const startLat = 10.78, startLng = 106.70;  // Điểm xuất phát
    const endLat = 10.80, endLng = 106.72;      // Điểm đích
    
    // ⭐ Gọi OSRM API (miễn phí, không cần API key)
    const url = `https://router.project-osrm.org/route/v1/driving/
        ${startLng},${startLat};${endLng},${endLat}
        ?overview=full&geometries=geojson`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    if (data.routes && data.routes.length > 0) {
        const route = data.routes[0];
        
        // ⭐ OSRM trả về [lng, lat], Leaflet cần [lat, lng]
        const coords = route.geometry.coordinates
            .map(c => [c[1], c[0]]);  // Đảo thứ tự
        
        // ⭐ Vẽ đường đi
        L.polyline(coords, {
            color: '#667eea',
            weight: 5,
            opacity: 0.8
        }).addTo(map);
        
        // Thông tin đường đi
        const distance = (route.distance / 1000).toFixed(2);  // km
        const duration = Math.round(route.duration / 60);     // phút
        
        console.log(`Khoảng cách: ${distance} km`);
        console.log(`Thời gian: ${duration} phút`);
    }
};
```

---

### 6.5. Vẽ vòng tròn (Circle) tìm kiếm

```javascript
// ⭐ Vẽ vòng tròn bán kính 2km
const circle = L.circle([10.78, 106.70], {
    radius: 2000,         // 2000 mét = 2km
    color: '#667eea',     // Màu viền
    fillOpacity: 0.1      // Độ trong suốt nền
}).addTo(map);

// Zoom fit vào vòng tròn
map.fitBounds(circle.getBounds());

// Xóa vòng tròn
map.removeLayer(circle);
```

---

## 7. API Endpoints

| Endpoint | Method | Mô tả | Ví dụ |
|----------|--------|-------|-------|
| `/` | GET | Trang bản đồ | - |
| `/api/loai/` | GET | Danh sách loại | - |
| `/api/quan/` | GET | Tất cả quán | - |
| `/api/timkiem/` | GET | Tìm theo vị trí | `?lat=10.78&lng=106.70&r=2` |
| `/api/goiy/<id>/` | GET | Gợi ý tương tự | `/api/goiy/1/` |
| `/admin/` | GET | Trang admin | - |

### Response format:

```json
{
    "status": "success",
    "data": [
        {
            "ma_quan": 1,
            "ten_quan": "Phở Hà Nội",
            "loai": "Phở",
            "diem": 4.5,
            "kinh_do": 106.70098,
            "vi_do": 10.77689,
            "khoang_cach": 1.25
        }
    ]
}
```

---

## 8. Cách chạy project

### 8.1. Yêu cầu
- Python 3.8+
- PostgreSQL + PostGIS
- pip packages: `django`, `psycopg2-binary`, `django-cors-headers`

### 8.2. Cài đặt

```bash
# 1. Cài packages
pip install django psycopg2-binary django-cors-headers

# 2. Di chuyển vào thư mục project
cd d:\WebGis\quanan_project

# 3. Chạy migrations (tạo bảng auth, session...)
python manage.py migrate

# 4. Tạo admin
python create_admin.py

# 5. Chạy server
python manage.py runserver 8000
```

### 8.3. Truy cập
- **Bản đồ:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/
  - Username: `admin`
  - Password: `123`

---

## Tổng kết kiến thức

| Công nghệ | Bạn đã học |
|-----------|------------|
| **Django** | Routing, Views, Models, Templates, JsonResponse |
| **PostgreSQL** | Kết nối, Raw SQL, LEFT JOIN |
| **PostGIS** | ST_X, ST_Y, ST_Distance, ST_DWithin, ST_MakePoint |
| **Leaflet.js** | Map, Marker, Popup, Circle, Polyline |
| **JavaScript** | fetch API, async/await, Geolocation |
| **OSRM** | Routing API miễn phí |

**Tiếp theo có thể học:**
- Django REST Framework (DRF) - API tốt hơn
- GeoDjango - Tích hợp GIS sâu hơn
- React/Vue.js - Frontend hiện đại
- Docker - Deployment
