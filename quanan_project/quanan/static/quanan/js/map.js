// map.js - Các hàm xử lý bản đồ và tìm kiếm

// Biến toàn cục
let map, markers = {}, dsQuan = [], dsQuanGoc = [], loaiHT = 'all', tuKhoa = '';
let circleLayer = null, startMarker = null, routeLayer = null;
let dangChonDiem = false, quanDuocChon = null;
const mau = { 'Phở': '#e74c3c', 'Bún': '#e67e22', 'Cơm': '#27ae60', 'Lẩu': '#9b59b6', 'Gà': '#f39c12', 'Cafe': '#3498db' };

// Bỏ dấu tiếng Việt
const boDau = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').toLowerCase();

// Khởi tạo bản đồ
const khoiTaoMap = (elementId, lat = 10.78, lng = 106.70, zoom = 13) => {
    map = L.map(elementId).setView([lat, lng], zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    // Xử lý click chọn điểm
    map.on('click', e => {
        if (dangChonDiem) {
            datDiemXuatPhat(e.latlng.lat, e.latlng.lng);
            dangChonDiem = false;
        }
    });

    return map;
};

// Lọc danh sách theo loại và từ khóa
const loc = () => {
    let d = dsQuan;
    if (loaiHT !== 'all') d = d.filter(q => q.loai === loaiHT);
    if (tuKhoa) d = d.filter(q => boDau(q.ten_quan || '').includes(boDau(tuKhoa)));
    return d;
};

// Đặt điểm xuất phát
const datDiemXuatPhat = (lat, lng) => {
    document.getElementById('start-lat').value = lat.toFixed(5);
    document.getElementById('start-lng').value = lng.toFixed(5);
    document.getElementById('start-status').innerHTML = `<span style="color:#27ae60">Đã chọn: ${lat.toFixed(5)}, ${lng.toFixed(5)}</span>`;

    if (startMarker) map.removeLayer(startMarker);
    startMarker = L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'start-marker',
            html: '<div style="width:20px;height:20px;background:#27ae60;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.3)"></div>',
            iconSize: [20, 20], iconAnchor: [10, 10]
        })
    }).addTo(map).bindPopup('Điểm xuất phát');
};

// Lấy vị trí hiện tại (GPS)
const layViTriHienTai = () => {
    document.getElementById('start-status').innerHTML = '<span style="color:#3498db">Đang lấy vị trí...</span>';
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            pos => {
                datDiemXuatPhat(pos.coords.latitude, pos.coords.longitude);
                map.flyTo([pos.coords.latitude, pos.coords.longitude], 15);
            },
            err => {
                document.getElementById('start-status').innerHTML = `<span style="color:#e74c3c">Lỗi: ${err.message}</span>`;
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    } else {
        document.getElementById('start-status').innerHTML = '<span style="color:#e74c3c">Trình duyệt không hỗ trợ</span>';
    }
};

// Bật chế độ chọn điểm trên bản đồ
const chonDiemXuatPhat = () => {
    dangChonDiem = true;
    document.getElementById('start-status').innerHTML = '<span style="color:#3498db">Click vào bản đồ để chọn...</span>';
};

// Hiển thị danh sách quán và markers
const hienThi = (data) => {
    Object.values(markers).forEach(m => map.removeLayer(m));
    markers = {};
    document.getElementById('count').textContent = data.length;

    document.getElementById('list').innerHTML = data.length ? data.map(q => `
        <div class="quan-card" data-ma="${q.ma_quan}" data-ten="${q.ten_quan}" data-lat="${q.vi_do}" data-lng="${q.kinh_do}">
            <h3>${q.ten_quan}</h3>
            <div class="meta">
                <span class="loai">${q.loai || 'Khác'}</span> 
                ⭐ ${q.diem.toFixed(1)} | ${'$'.repeat(q.muc_gia || 1)}
                ${q.khoang_cach ? ' | ' + q.khoang_cach + ' km' : ''}
            </div>
        </div>
    `).join('') : '<p style="color:#888;font-size:12px">Không tìm thấy</p>';

    data.forEach(q => {
        if (q.vi_do && q.kinh_do) {
            const m = L.circleMarker([q.vi_do, q.kinh_do], {
                radius: 8, fillColor: mau[q.loai] || '#888', color: '#fff', weight: 2, fillOpacity: 0.9
            }).bindPopup(`<b>${q.ten_quan}</b><br>${q.loai || 'Khác'} | ⭐ ${q.diem.toFixed(1)}<br>${q.dia_chi || ''}`);
            m.addTo(map);
            markers[q.ma_quan] = m;
        }
    });

    // Gắn sự kiện click cho card
    document.querySelectorAll('.quan-card').forEach(card => {
        card.onclick = () => {
            const ma = card.dataset.ma;
            const ten = card.dataset.ten;
            const lat = parseFloat(card.dataset.lat);
            const lng = parseFloat(card.dataset.lng);

            if (markers[ma]) {
                map.flyTo([lat, lng], 16);
                markers[ma].openPopup();
            }

            quanDuocChon = { ma, ten, lat, lng };
            document.getElementById('route-target').innerHTML = `<span style="color:#fff">Đến: ${ten}</span>`;
            document.getElementById('btn-route').style.display = 'block';

            loadGoiY(ma);
        };
    });
};

// Load gợi ý quán tương tự
const loadGoiY = async (ma) => {
    const container = document.getElementById('goiy-list');
    container.innerHTML = '<i style="color:#888;font-size:11px">Đang tải...</i>';

    const res = await fetch(`/api/goiy/${ma}/`);
    const json = await res.json();

    if (json.data && json.data.length) {
        container.innerHTML = json.data.map(q => `
            <div class="goiy-card" onclick="flyTo(${q.vi_do},${q.kinh_do},${q.ma_quan},'${q.ten_quan.replace(/'/g, "\\'")}')">
                ${q.ten_quan}<br>
                <span style="color:#888">${q.loai || 'Khác'} | ⭐ ${q.diem.toFixed(1)}</span>
            </div>
        `).join('');
    } else {
        container.innerHTML = '<i style="color:#888;font-size:11px">Không có quán cùng loại</i>';
    }
};

// Bay đến quán
const flyTo = (lat, lng, ma, ten) => {
    map.flyTo([lat, lng], 16);
    if (markers[ma]) markers[ma].openPopup();
    quanDuocChon = { ma, ten, lat, lng };
    document.getElementById('route-target').innerHTML = `<span style="color:#fff">Đến: ${ten}</span>`;
    document.getElementById('btn-route').style.display = 'block';
};

// Tìm quán theo vị trí và bán kính
const timTheoViTri = async () => {
    const lat = parseFloat(document.getElementById('start-lat').value);
    const lng = parseFloat(document.getElementById('start-lng').value);
    const r = document.getElementById('radius').value;

    if (!lat || !lng) {
        alert('Vui lòng chọn điểm xuất phát trước');
        return;
    }

    if (circleLayer) map.removeLayer(circleLayer);
    circleLayer = L.circle([lat, lng], { radius: r * 1000, color: '#667eea', fillOpacity: 0.1 }).addTo(map);

    const res = await fetch(`/api/timkiem/?lat=${lat}&lng=${lng}&r=${r}`);
    const json = await res.json();

    if (json.data) {
        dsQuan = json.data;
        hienThi(dsQuan);
        map.fitBounds(circleLayer.getBounds());
        document.getElementById('btn-tat').style.display = 'block';
    }
};

// Tắt tìm kiếm theo vị trí
const tatTimKiem = () => {
    if (circleLayer) map.removeLayer(circleLayer);
    circleLayer = null;
    dsQuan = dsQuanGoc;
    hienThi(loc());
    document.getElementById('btn-tat').style.display = 'none';
};

// Tìm đường bằng OSRM
const timDuong = async () => {
    const startLat = parseFloat(document.getElementById('start-lat').value);
    const startLng = parseFloat(document.getElementById('start-lng').value);

    if (!startLat || !startLng) {
        alert('Vui lòng chọn điểm xuất phát');
        return;
    }
    if (!quanDuocChon) {
        alert('Vui lòng chọn quán đích');
        return;
    }

    const { lat: endLat, lng: endLng } = quanDuocChon;
    const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;

    try {
        const res = await fetch(url);
        const json = await res.json();

        if (json.routes && json.routes.length > 0) {
            const route = json.routes[0];
            const coords = route.geometry.coordinates.map(c => [c[1], c[0]]);

            if (routeLayer) map.removeLayer(routeLayer);
            routeLayer = L.polyline(coords, { color: '#667eea', weight: 5, opacity: 0.8 }).addTo(map);

            const dist = (route.distance / 1000).toFixed(2);
            const time = Math.round(route.duration / 60);

            // Popup hiển thị thông tin giữa đường
            const midIndex = Math.floor(coords.length / 2);
            const midPoint = coords[midIndex];
            const routeInfoPopup = L.popup({ closeButton: false, autoClose: false, closeOnClick: false })
                .setLatLng(midPoint)
                .setContent(`<div style="text-align:center;font-weight:bold;font-size:14px;color:#667eea">${dist} km<br>${time} phút</div>`)
                .addTo(map);
            routeLayer.infoPopup = routeInfoPopup;

            map.fitBounds(routeLayer.getBounds().pad(0.1));

            document.getElementById('route-dist').textContent = dist + ' km';
            document.getElementById('route-time').textContent = time + ' phút';
            document.getElementById('route-info').style.display = 'block';
            document.getElementById('btn-clear-route').style.display = 'block';
        }
    } catch (err) {
        alert('Lỗi tìm đường: ' + err.message);
    }
};

// Xóa đường đi
const xoaDuong = () => {
    if (routeLayer) {
        if (routeLayer.infoPopup) map.removeLayer(routeLayer.infoPopup);
        map.removeLayer(routeLayer);
    }
    routeLayer = null;
    document.getElementById('route-info').style.display = 'none';
    document.getElementById('btn-clear-route').style.display = 'none';
};

// Load danh sách loại quán
const loadLoaiQuan = () => {
    fetch('/api/loai/').then(r => r.json()).then(j => {
        j.data.forEach(l => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.dataset.loai = l.ten_loai;
            btn.textContent = l.ten_loai;
            btn.onclick = () => {
                loaiHT = l.ten_loai;
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                hienThi(loc());
            };
            document.getElementById('filters').appendChild(btn);
        });
    });
};

// Load danh sách quán
const loadDanhSachQuan = () => {
    fetch('/api/quan/').then(r => r.json()).then(j => {
        dsQuan = j.data;
        dsQuanGoc = j.data;
        hienThi(dsQuan);
    });
};

// Khởi tạo sự kiện
const khoiTaoSuKien = () => {
    document.querySelector('[data-loai="all"]').onclick = () => {
        loaiHT = 'all';
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('[data-loai="all"]').classList.add('active');
        hienThi(loc());
    };

    document.getElementById('search').oninput = e => {
        tuKhoa = e.target.value;
        hienThi(loc());
    };
};
