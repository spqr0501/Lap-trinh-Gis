# Custom GIS Tools Documentation

## Tổng Quan

Thư viện GIS Tools tự viết **không sử dụng thư viện bên ngoài** (chỉ dùng `math` của Python standard library).

## File: `utils/gis_tools.py`

### Class: `GISTools`

#### 1. `haversine_distance(lat1, lon1, lat2, lon2)`

**Mục đích:** Tính khoảng cách giữa 2 điểm trên trái đất

**Công thức:** Haversine Formula

**Input:**
- `lat1, lon1`: Tọa độ điểm 1 (độ)
- `lat2, lon2`: Tọa độ điểm 2 (độ)

**Output:** Khoảng cách (km)

**Ví dụ:**
```python
from ThucHanhApp.utils.gis_tools import distance_km

# Khoảng cách từ Đà Nẵng đến Hội An
distance = distance_km(16.0544, 108.2022, 15.8801, 108.3380)
print(f"{distance:.2f} km")  # ~20 km
```

**API Example:**
```
GET /api/gis-tools/?tool=distance&lat1=16.05&lon1=108.20&lat2=15.88&lon2=108.34
```

---

#### 2. `find_nearest_point(origin_lat, origin_lon, points)`

**Mục đích:** Tìm điểm gần nhất từ danh sách

**Input:**
- `origin_lat, origin_lon`: Tọa độ gốc
- `points`: List các điểm `[(lat, lon, data), ...]`

**Output:** `(nearest_point, distance)`

**Ví dụ:**
```python
stores = [(16.05, 108.20, "Store A"), (16.06, 108.21, "Store B")]
nearest, dist = GISTools.find_nearest_point(16.055, 108.205, stores)
print(f"Cửa hàng gần nhất: {nearest[2]}, cách {dist:.2f} km")
```

**API Example:**
```
GET /api/gis-tools/?tool=nearest&lat=16.05&lon=108.20
```

---

#### 3. `point_in_polygon(point_lat, point_lon, polygon_coords)`

**Mục đích:** Kiểm tra điểm có nằm trong polygon không

**Thuật toán:** Ray Casting Algorithm

**Input:**
- `point_lat, point_lon`: Tọa độ điểm cần kiểm tra
- `polygon_coords`: List tọa độ `[(lat, lon), ...]` tạo thành polygon

**Output:** `True` nếu điểm trong polygon, `False` nếu ngoài

**Ví dụ:**
```python
# Định nghĩa khu vực Đà Nẵng (hình chữ nhật đơn giản)
da_nang_area = [
    (16.10, 108.15),
    (16.10, 108.30),
    (16.00, 108.30),
    (16.00, 108.15),
]

point = (16.05, 108.20)
is_inside = GISTools.point_in_polygon(point[0], point[1], da_nang_area)
print(f"Điểm nằm trong khu vực: {is_inside}")
```

---

#### 4. `calculate_polygon_area(polygon_coords)`

**Mục đích:** Tính diện tích polygon

**Công thức:** Shoelace Formula

**Input:** `polygon_coords` - List `[(lat, lon), ...]`

**Output:** Diện tích (km²)

**Ví dụ:**
```python
area_coords = [(16.05, 108.20), (16.06, 108.20), (16.06, 108.21), (16.05, 108.21)]
area = GISTools.calculate_polygon_area(area_coords)
print(f"Diện tích: {area:.2f} km²")
```

---

#### 5. `create_circle_buffer(center_lat, center_lon, radius_km, num_points=32)`

**Mục đích:** Tạo vùng đệm (buffer) hình tròn xung quanh điểm

**Input:**
- `center_lat, center_lon`: Tâm
- `radius_km`: Bán kính (km)
- `num_points`: Số điểm tạo thành đường tròn (mặc định 32)

**Output:** List tọa độ `[(lat, lon), ...]` tạo thành đường tròn

**Ví dụ:**
```python
# Tạo vùng đệm 5km quanh cửa hàng
buffer = GISTools.create_circle_buffer(16.05, 108.20, 5.0)
# Có thể dùng buffer này để vẽ trên bản đồ hoặc kiểm tra point_in_polygon
```

**API Example:**
```
GET /api/gis-tools/?tool=buffer&lat=16.05&lon=108.20&radius=5
```

---

#### 6. `calculate_centroid(points)`

**Mục đích:** Tính điểm trung tâm (centroid) của nhiều điểm

**Input:** `points` - List `[(lat, lon), ...]`

**Output:** `(center_lat, center_lon)`

**Ví dụ:**
```python
stores = [(16.05, 108.20), (16.06, 108.21), (16.04, 108.19)]
center_lat, center_lon = GISTools.calculate_centroid(stores)
print(f"Tâm: ({center_lat:.4f}, {center_lon:.4f})")
```

**API Example:**
```
GET /api/gis-tools/?tool=centroid
# Tính tâm của tất cả cửa hàng trong database
```

---

#### 7. `calculate_bearing(lat1, lon1, lat2, lon2)`

**Mục đích:** Tính hướng đi từ điểm 1 đến điểm 2

**Output:** Góc (0-360°) với 0° là Bắc, 90° là Đông

**Ví dụ:**
```python
bearing = GISTools.calculate_bearing(16.05, 108.20, 16.06, 108.21)
print(f"Hướng: {bearing:.1f}°")  # VD: 45° = Đông Bắc
```

**API Example:**
```
GET /api/gis-tools/?tool=bearing&lat1=16.05&lon1=108.20&lat2=16.06&lon2=108.21
# Response: {bearing_degrees: 45.0, direction: "Đông Bắc"}
```

---

#### 8. `get_bounding_box(points, padding_km=0)`

**Mục đích:** Lấy khung bao (bounding box) cho tập điểm

**Input:**
- `points`: List `[(lat, lon), ...]`
- `padding_km`: Khoảng đệm thêm (km)

**Output:** `((min_lat, min_lon), (max_lat, max_lon))`

**Ví dụ:**
```python
stores = [(16.05, 108.20), (16.10, 108.25), (16.03, 108.18)]
bbox = GISTools.get_bounding_box(stores, padding_km=1)
print(f"Bounding box: {bbox}")
# Dùng để fit map bounds
```

---

#### 9. `points_within_radius(origin_lat, origin_lon, points, radius_km)`

**Mục đích:** Tìm tất cả điểm trong bán kính cho trước

**Input:**
- `origin_lat, origin_lon`: Điểm gốc
- `points`: List `[(lat, lon, data), ...]`
- `radius_km`: Bán kính (km)

**Output:** List dict `[{'point': ..., 'distance': ...}, ...]` sắp xếp theo khoảng cách

**Ví dụ:**
```python
results = GISTools.points_within_radius(16.05, 108.20, stores, 10.0)
for r in results:
    print(f"{r['point'][2]}: {r['distance']:.2f} km")
```

**API Example:**
```
GET /api/gis-tools/?tool=within_radius&lat=16.05&lon=108.20&radius=10
# Tìm cửa hàng trong bán kính 10km
```

---

#### 10. `simplify_line(points, tolerance=0.0001)`

**Mục đích:** Đơn giản hóa đường (giảm số điểm) giữ nguyên hình dạng

**Thuật toán:** Douglas-Peucker Algorithm

**Input:**
- `points`: List `[(lat, lon), ...]`
- `tolerance`: Độ chính xác (càng lớn càng đơn giản)

**Output:** List điểm đã được đơn giản hóa

**Ví dụ:**
```python
# Route có 1000 điểm
route = [(16.05, 108.20), (16.051, 108.201), ..., (16.06, 108.25)]
simplified = GISTools.simplify_line(route, tolerance=0.001)
print(f"Giảm từ {len(route)} xuống {len(simplified)} điểm")
```

---

## API Endpoints

### Base URL: `/api/gis-tools/`

All endpoints return JSON:

```json
{
  "success": true/false,
  "tool": "tool_name",
  "result": {...},
  "error": "error message (if any)"
}
```

### Available Tools:

1. **`distance`** - Tính khoảng cách
   - Params: `lat1, lon1, lat2, lon2`
   
2. **`nearest`** - Tìm cửa hàng gần nhất
   - Params: `lat, lon`
   
3. **`buffer`** - Tạo vùng đệm
   - Params: `lat, lon, radius`
   
4. **`centroid`** - Tính tâm tất cả cửa hàng
   - Params: (none)
   
5. **`within_radius`** - Cửa hàng trong bán kính
   - Params: `lat, lon, radius`
   
6. **`bearing`** - Tính hướng đi
   - Params: `lat1, lon1, lat2, lon2`

### Example Usage:

```javascript
// Tìm cửa hàng gần vị trí người dùng
fetch('/api/gis-tools/?tool=nearest&lat=16.05&lon=108.20')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('Cửa hàng gần nhất:', data.result.store_name);
      console.log('Khoảng cách:', data.result.distance_km, 'km');
    }
  });

// Tìm tất cả cửa hàng trong vòng 5km
fetch('/api/gis-tools/?tool=within_radius&lat=16.05&lon=108.20&radius=5')
  .then(response => response.json())
  .then(data => {
    console.log(`Tìm thấy ${data.result.count} cửa hàng`);
    data.result.stores.forEach(store => {
      console.log(`- ${store.store_name}: ${store.distance_km} km`);
    });
  });
```

## Implementation Details

### Không sử dụng thư viện bên ngoài

Tất cả các hàm được implement từ đầu chỉ dùng:
- `math.sin`, `math.cos`, `math.atan2`, `math.sqrt` - Trigonometry cơ bản
- `math.radians`, `math.degrees` - Chuyển đổi đơn vị
- Python built-in functions

### Độ chính xác

- **Haversine Formula:** Chính xác cho khoảng cách < 1000km
- **Point in Polygon:** 100% chính xác với ray casting
- **Buffer Circle:** Gần đúng (giả định trái đất là hình cầu hoàn hảo)
- **Polygon Area:** Gần đúng cho polygon nhỏ (< 100km²)

### Performance

- **Distance calculation:** O(1)
- **Find nearest:** O(n) với n = số điểm
- **Point in polygon:** O(m) với m = số cạnh polygon
- **Within radius:** O(n)
- **Douglas-Peucker:** O(n log n) best case, O(n²) worst case

## Sử Dụng Trong Project

### Import
```python
from ThucHanhApp.utils.gis_tools import GISTools, distance_km
```

### Trong Views
```python
# Tìm cửa hàng gần nhất
stores = CuaHang.objects.filter(geom__isnull=False)
points = [(s.geom.y, s.geom.x, s) for s in stores]
nearest, dist = GISTools.find_nearest_point(user_lat, user_lon, points)
```

### Trong Templates (via API)
```javascript
fetch('/api/gis-tools/?tool=nearest&lat=' + userLat + '&lon=' + userLon)
  .then(response => response.json())
  .then(data => {
    // Use data.result
  });
```

## Testing

Mở browser console và test:

```javascript
// Test 1: Calculate distance
fetch('/api/gis-tools/?tool=distance&lat1=16.05&lon1=108.20&lat2=16.06&lon2=108.21')
  .then(r => r.json()).then(console.log);

// Test 2: Find nearest store
fetch('/api/gis-tools/?tool=nearest&lat=16.05&lon=108.20')
  .then(r => r.json()).then(console.log);

// Test 3: Stores within 10km
fetch('/api/gis-tools/?tool=within_radius&lat=16.05&lon=108.20&radius=10')
  .then(r => r.json()).then(console.log);
```
