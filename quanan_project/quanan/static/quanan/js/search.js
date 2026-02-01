// search.js - Các hàm cho trang tìm kiếm

// Biến toàn cục
let mapSearch, searchMarker = null, searchCircle = null, resultMarkers = [];

// Khởi tạo bản đồ tìm kiếm
const khoiTaoMapSearch = (elementId, lat = 10.78, lng = 106.70, zoom = 13) => {
    mapSearch = L.map(elementId).setView([lat, lng], zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(mapSearch);

    // Click trên bản đồ để chọn vị trí
    mapSearch.on('click', (e) => {
        document.getElementById('lat').value = e.latlng.lat.toFixed(5);
        document.getElementById('lng').value = e.latlng.lng.toFixed(5);
        datMarkerTimKiem(e.latlng.lat, e.latlng.lng);
    });

    return mapSearch;
};

// Đặt marker vị trí tìm kiếm
const datMarkerTimKiem = (lat, lng) => {
    if (searchMarker) mapSearch.removeLayer(searchMarker);

    searchMarker = L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'search-marker',
            html: '<div style="width:20px;height:20px;background:#e74c3c;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.3)"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        })
    }).addTo(mapSearch);

    searchMarker.bindPopup('Vị trí tìm kiếm').openPopup();
};

// Vẽ vòng tròn bán kính
const veVongTron = (lat, lng, radiusKm) => {
    if (searchCircle) mapSearch.removeLayer(searchCircle);

    searchCircle = L.circle([lat, lng], {
        radius: radiusKm * 1000,
        color: '#667eea',
        fillColor: '#667eea',
        fillOpacity: 0.1,
        weight: 2
    }).addTo(mapSearch);
};

// Hiển thị kết quả tìm kiếm
const hienThiKetQua = (data) => {
    // Xóa markers cũ
    resultMarkers.forEach(m => mapSearch.removeLayer(m));
    resultMarkers = [];

    const container = document.getElementById('quan-list');
    const countEl = document.getElementById('result-count');

    countEl.style.display = 'block';
    countEl.querySelector('span').textContent = data.length;

    if (data.length === 0) {
        container.innerHTML = '<div style="color:#888;text-align:center;padding:20px;font-style:italic">Không tìm thấy quán ăn trong bán kính</div>';
        return;
    }

    // Hiển thị list
    container.innerHTML = data.map(quan => `
        <div class="quan-card" data-lat="${quan.vi_do}" data-lng="${quan.kinh_do}">
            <h3>${quan.ten_quan}</h3>
            <div class="meta">
                <span>${quan.loai || 'Khác'}</span>
                <span>⭐ ${quan.diem.toFixed(1)}</span>
                <span class="khoang-cach">${quan.khoang_cach} km</span>
            </div>
        </div>
    `).join('');

    // Thêm markers
    data.forEach((quan, idx) => {
        if (quan.vi_do && quan.kinh_do) {
            const marker = L.marker([quan.vi_do, quan.kinh_do], {
                icon: L.divIcon({
                    className: 'result-marker',
                    html: `<div style="
                        width:28px;height:28px;
                        background:#27ae60;
                        border-radius:50%;
                        border:2px solid #fff;
                        display:flex;align-items:center;justify-content:center;
                        color:#fff;font-weight:bold;font-size:12px;
                        box-shadow:0 2px 5px rgba(0,0,0,0.3);
                    ">${idx + 1}</div>`,
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                })
            }).addTo(mapSearch);

            marker.bindPopup(`
                <b>${quan.ten_quan}</b><br>
                ${quan.loai || 'Khác'} | ⭐ ${quan.diem.toFixed(1)}<br>
                ${quan.khoang_cach} km
            `);

            resultMarkers.push(marker);
        }
    });

    // Click event cho cards
    container.querySelectorAll('.quan-card').forEach((card, idx) => {
        card.addEventListener('click', () => {
            const lat = parseFloat(card.dataset.lat);
            const lng = parseFloat(card.dataset.lng);
            if (lat && lng) {
                mapSearch.flyTo([lat, lng], 16);
                if (resultMarkers[idx]) {
                    resultMarkers[idx].openPopup();
                }
            }
        });
    });
};

// Tìm kiếm theo vị trí
const timKiem = async () => {
    const lat = parseFloat(document.getElementById('lat').value);
    const lng = parseFloat(document.getElementById('lng').value);
    const radius = parseFloat(document.getElementById('radius').value);

    if (isNaN(lat) || isNaN(lng) || isNaN(radius)) {
        alert('Vui lòng nhập đúng tọa độ và bán kính');
        return;
    }

    datMarkerTimKiem(lat, lng);
    veVongTron(lat, lng, radius);

    try {
        const res = await fetch(`/api/timkiem/?lat=${lat}&lng=${lng}&r=${radius}`);
        const json = await res.json();

        if (json.status === 'success') {
            hienThiKetQua(json.data);
            if (searchCircle) {
                mapSearch.fitBounds(searchCircle.getBounds().pad(0.1));
            }
        } else {
            alert('Lỗi: ' + json.message);
        }
    } catch (err) {
        console.error(err);
        alert('Lỗi kết nối server');
    }
};

// Lấy vị trí hiện tại
const layViTriSearch = () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                document.getElementById('lat').value = lat.toFixed(5);
                document.getElementById('lng').value = lng.toFixed(5);
                mapSearch.flyTo([lat, lng], 15);
                datMarkerTimKiem(lat, lng);
            },
            (err) => {
                alert('Không thể lấy vị trí: ' + err.message);
            }
        );
    } else {
        alert('Trình duyệt không hỗ trợ Geolocation');
    }
};

// Khởi tạo sự kiện cho trang tìm kiếm
const khoiTaoSuKienSearch = () => {
    document.getElementById('btn-search').addEventListener('click', timKiem);
    document.getElementById('btn-myloc').addEventListener('click', layViTriSearch);

    // Enter key
    document.querySelectorAll('.search-form input').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') timKiem();
        });
    });
};
