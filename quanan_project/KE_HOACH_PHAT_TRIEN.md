# KẾ HOẠCH PHÁT TRIỂN DỰ ÁN WEBGIS QUÁN ĂN

## 📌 Tổng quan dự án hiện tại

### Tính năng đã hoàn thành ✅
- [x] Hiển thị bản đồ với Leaflet.js
- [x] Xem danh sách quán ăn
- [x] Lọc theo loại quán
- [x] Tìm kiếm theo tên
- [x] Tìm quán theo vị trí + bán kính
- [x] Gợi ý quán tương tự (cùng loại)
- [x] Chỉ đường từ điểm xuất phát đến quán
- [x] Lấy vị trí hiện tại (GPS)
- [x] Trang Admin quản lý dữ liệu

---

## 🚀 Giai đoạn 1: Cải thiện Backend (2-3 tuần)

### 1.1. Chuyển sang Django REST Framework (DRF)
**Mục tiêu:** API chuẩn REST, có serializer, pagination, authentication

**Các task:**
- [ ] Cài đặt `djangorestframework`
- [ ] Tạo serializers cho các model
- [ ] Chuyển views thành ViewSets
- [ ] Thêm pagination cho danh sách quán
- [ ] Thêm filtering và ordering

**Code mẫu:**
```python
# serializers.py
from rest_framework import serializers
from .models import QuanAn, LoaiQuan

class QuanAnSerializer(serializers.ModelSerializer):
    loai = serializers.CharField(source='ma_loai.ten_loai')
    kinh_do = serializers.SerializerMethodField()
    vi_do = serializers.SerializerMethodField()
    
    class Meta:
        model = QuanAn
        fields = ['ma_quan', 'ten_quan', 'loai', 'diem_danh_gia', 'kinh_do', 'vi_do']
```

### 1.2. Thêm Authentication & Authorization
**Mục tiêu:** User đăng nhập, phân quyền

**Các task:**
- [ ] Tạo model UserProfile mở rộng User
- [ ] API đăng ký / đăng nhập / đăng xuất
- [ ] JWT Token authentication
- [ ] Phân quyền: Admin, User, Guest

### 1.3. Chuyển sang GeoDjango (Nâng cao)
**Mục tiêu:** Tích hợp GIS sâu hơn vào Django

**Các task:**
- [ ] Cài đặt `django.contrib.gis`
- [ ] Thay models.py bằng gis models
- [ ] Sử dụng PointField thay vì raw SQL
- [ ] Dùng GeoQuerySet cho spatial queries

**Code mẫu:**
```python
from django.contrib.gis.db import models

class QuanAn(models.Model):
    ten_quan = models.CharField(max_length=200)
    vi_tri = models.PointField(srid=4326)  # ⭐ GeoDjango field
```

---

## 🎨 Giai đoạn 2: Cải thiện Frontend (2-3 tuần)

### 2.1. Responsive Design
**Mục tiêu:** Hoạt động tốt trên mobile

**Các task:**
- [ ] Media queries cho màn hình nhỏ
- [ ] Sidebar thu gọn trên mobile
- [ ] Touch-friendly controls
- [ ] Bottom sheet cho danh sách

### 2.2. Cải thiện UX/UI
**Mục tiêu:** Giao diện đẹp hơn, dễ dùng hơn

**Các task:**
- [ ] Loading skeleton khi đang tải
- [ ] Animation khi chuyển view
- [ ] Dark mode toggle
- [ ] Hiển thị hình ảnh quán ăn
- [ ] Rating stars interactive
- [ ] Drag & drop marker điểm xuất phát

### 2.3. Chuyển sang React/Vue.js (Tùy chọn)
**Mục tiêu:** Frontend SPA hiện đại

**Các task:**
- [ ] Setup Vite + React hoặc Vue
- [ ] Tách components: Map, Sidebar, Card...
- [ ] State management (Redux/Vuex/Zustand)
- [ ] React-Leaflet hoặc Vue-Leaflet

---

## 📱 Giai đoạn 3: Tính năng mới (3-4 tuần)

### 3.1. Hệ thống đánh giá & bình luận
**Mục tiêu:** User có thể đánh giá và bình luận quán ăn

**Các task:**
- [ ] Model DanhGia: user, quan, diem, noi_dung, ngay_tao
- [ ] API CRUD đánh giá
- [ ] Tính điểm trung bình khi có đánh giá mới
- [ ] Hiển thị danh sách bình luận
- [ ] Lọc quán theo điểm đánh giá

**Database:**
```sql
CREATE TABLE danh_gia (
    id SERIAL PRIMARY KEY,
    ma_user INT REFERENCES auth_user(id),
    ma_quan INT REFERENCES quan_an(ma_quan),
    diem INT CHECK (diem >= 1 AND diem <= 5),
    noi_dung TEXT,
    ngay_tao TIMESTAMP DEFAULT NOW()
);
```

### 3.2. Yêu thích & Lịch sử
**Mục tiêu:** Lưu quán yêu thích, xem lại lịch sử

**Các task:**
- [ ] Model QuanYeuThich: user, quan
- [ ] Model LichSuXem: user, quan, thoi_gian
- [ ] API thêm/xóa yêu thích
- [ ] Trang "Quán yêu thích của tôi"
- [ ] Gợi ý dựa trên lịch sử xem

### 3.3. Tìm kiếm nâng cao
**Mục tiêu:** Lọc theo nhiều tiêu chí

**Các task:**
- [ ] Lọc theo mức giá ($ - $$$$$)
- [ ] Lọc theo điểm đánh giá (>4 sao)
- [ ] Lọc theo khoảng cách
- [ ] Lọc theo giờ mở cửa
- [ ] Full-text search tên + mô tả

### 3.4. Hiển thị menu quán ăn
**Mục tiêu:** Xem thực đơn, giá món

**Các task:**
- [ ] Model ThucDon: ma_quan, ten_mon, gia, hinh_anh
- [ ] API lấy menu theo quán
- [ ] Popup/Modal hiển thị menu
- [ ] Tìm quán có món X

---

## 🔧 Giai đoạn 4: Nâng cao & Triển khai (2-3 tuần)

### 4.1. Caching & Performance
**Mục tiêu:** Tăng tốc độ, giảm tải server

**Các task:**
- [ ] Redis cache cho API results
- [ ] Lazy loading markers (cluster)
- [ ] CDN cho static files
- [ ] Database indexing (spatial index)

### 4.2. Logging & Monitoring
**Mục tiêu:** Theo dõi hệ thống

**Các task:**
- [ ] Sentry cho error tracking
- [ ] Logging API requests
- [ ] Analytics: quán được xem nhiều nhất
- [ ] Health check endpoint

### 4.3. Triển khai Production
**Mục tiêu:** Deploy lên server thật

**Các task:**
- [ ] Dockerize ứng dụng
- [ ] Docker Compose: Django + PostgreSQL + Nginx
- [ ] CI/CD với GitHub Actions
- [ ] Deploy lên VPS (DigitalOcean, AWS, GCP)
- [ ] SSL certificate (Let's Encrypt)
- [ ] Domain name setup

**Docker Compose mẫu:**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
  db:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: quan_an
      POSTGRES_PASSWORD: 123456
  nginx:
    image: nginx
    ports:
      - "80:80"
```

---

## 📊 Giai đoạn 5: Mở rộng (Dài hạn)

### 5.1. Mobile App
- [ ] React Native hoặc Flutter
- [ ] Push notifications
- [ ] Offline mode

### 5.2. AI/ML Features
- [ ] Gợi ý cá nhân hóa
- [ ] Phân tích sentiment bình luận
- [ ] Dự đoán độ đông đúc

### 5.3. Tích hợp bên ngoài
- [ ] Google Maps Places API
- [ ] Đặt bàn online
- [ ] Thanh toán online
- [ ] Chia sẻ social media

---

## 📅 Timeline tổng quan

| Giai đoạn | Thời gian | Ưu tiên |
|-----------|-----------|---------|
| 1. Backend improvements | 2-3 tuần | ⭐⭐⭐ Cao |
| 2. Frontend improvements | 2-3 tuần | ⭐⭐⭐ Cao |
| 3. Tính năng mới | 3-4 tuần | ⭐⭐ Trung bình |
| 4. Triển khai | 2-3 tuần | ⭐⭐⭐ Cao |
| 5. Mở rộng | Dài hạn | ⭐ Thấp |

---

## 📚 Tài liệu tham khảo

### Django
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [GeoDjango](https://docs.djangoproject.com/en/4.2/ref/contrib/gis/)

### PostGIS
- [PostGIS Documentation](https://postgis.net/documentation/)
- [PostGIS Functions](https://postgis.net/docs/reference.html)

### Leaflet.js
- [Leaflet Documentation](https://leafletjs.com/reference.html)
- [Leaflet Plugins](https://leafletjs.com/plugins.html)

### Deployment
- [Docker Documentation](https://docs.docker.com/)
- [DigitalOcean Django Deployment](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04)
