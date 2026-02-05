/**
 * GIS Tools JavaScript Library
 * Cac cong cu GIS cho ban do va tim duong
 */

// Bien toan cuc
var ban_do = null;
var du_lieu_cua_hang = [];
var vi_tri_nguoi_dung = null;
var dau_hieu_nguoi_dung = null;

// Cac dau hieu cho tim duong
var dau_hieu_bat_dau = null;
var dau_hieu_ket_thuc = null;
var duong_di = null;
var dang_chon_diem_bat_dau = false;
var dang_chon_diem_ket_thuc = false;
var toa_do_bat_dau = null;
var toa_do_ket_thuc = null;

/**
 * Ham tinh khoang cach giua 2 diem bang cong thuc Haversine
 * @param {number} vi_do_1 - Vi do diem 1
 * @param {number} kinh_do_1 - Kinh do diem 1
 * @param {number} vi_do_2 - Vi do diem 2
 * @param {number} kinh_do_2 - Kinh do diem 2
 * @returns {number} Khoang cach tinh bang km
 */
function tinh_khoang_cach(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2) {
    var R = 6371; // Ban kinh trai dat (km)
    var d_vi_do = (vi_do_2 - vi_do_1) * Math.PI / 180;
    var d_kinh_do = (kinh_do_2 - kinh_do_1) * Math.PI / 180;
    var a = Math.sin(d_vi_do / 2) * Math.sin(d_vi_do / 2) +
        Math.cos(vi_do_1 * Math.PI / 180) * Math.cos(vi_do_2 * Math.PI / 180) *
        Math.sin(d_kinh_do / 2) * Math.sin(d_kinh_do / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    var khoang_cach = R * c;
    return khoang_cach;
}

/**
 * Tim vi tri nguoi dung (manual - khi bam nut)
 */
function tim_vi_tri_nguoi_dung() {
    if (!navigator.geolocation) {
        alert('Trình duyệt không hỗ trợ geolocation');
        return;
    }

    document.getElementById('user-coords').textContent = 'Đang tìm...';

    navigator.geolocation.getCurrentPosition(
        function (vi_tri) {
            vi_tri_nguoi_dung = {
                vi_do: vi_tri.coords.latitude,
                kinh_do: vi_tri.coords.longitude
            };

            // Cap nhat UI
            document.getElementById('user-coords').textContent =
                vi_tri_nguoi_dung.vi_do.toFixed(5) + ', ' + vi_tri_nguoi_dung.kinh_do.toFixed(5);

            // Hien thi thong bao
            document.getElementById('user-location-info').style.display = 'block';

            // Them dau hieu nguoi dung
            if (dau_hieu_nguoi_dung) {
                ban_do.removeLayer(dau_hieu_nguoi_dung);
            }

            dau_hieu_nguoi_dung = L.marker([vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                })
            }).addTo(ban_do);
            dau_hieu_nguoi_dung.bindPopup("<b>Vị trí của bạn</b>");

            // Di chuyen ban do den vi tri nguoi dung
            ban_do.setView([vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do], 14);

            // AUTO-SET STARTING POINT cho routing
            dat_diem_bat_dau(vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do);

            // Tinh khoang cach va hien thi danh sach
            tinh_khoang_cach_cac_cua_hang();
            hien_thi_danh_sach_cua_hang('type-filter', 'store-list');
        },
        function (loi) {
            console.error('Loi geolocation:', loi);
            document.getElementById('user-coords').textContent = 'Không thể xác định vị trí';
            alert('Không thể xác định vị trí của bạn. Vui lòng cho phép truy cập vị trí.');
        }
    );
}


/**
 * Khoi tao ban do Leaflet
 * @param {string} id_container - ID cua div container
 * @param {number} vi_do - Vi do trung tam
 * @param {number} kinh_do - Kinh do trung tam
 * @param {number} muc_zoom - Muc zoom
 */
function khoi_tao_ban_do(id_container, vi_do, kinh_do, muc_zoom) {
    ban_do = L.map(id_container).setView([vi_do, kinh_do], muc_zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(ban_do);

    // Gan su kien click cho chon diem
    ban_do.on('click', function (su_kien) {
        if (dang_chon_diem_bat_dau) {
            dat_diem_bat_dau(su_kien.latlng.lat, su_kien.latlng.lng);
            dang_chon_diem_bat_dau = false;
            ban_do.getContainer().style.cursor = '';
        } else if (dang_chon_diem_ket_thuc) {
            dat_diem_ket_thuc(su_kien.latlng.lat, su_kien.latlng.lng);
            dang_chon_diem_ket_thuc = false;
            ban_do.getContainer().style.cursor = '';
        }
    });

    return ban_do;
}

/**
 * Tinh khoang cach cho tat ca cac cua hang
 */
function tinh_khoang_cach_cac_cua_hang() {
    if (!vi_tri_nguoi_dung) return;

    du_lieu_cua_hang.forEach(function (cua_hang) {
        if (cua_hang.vi_do && cua_hang.kinh_do) {
            cua_hang.khoang_cach = tinh_khoang_cach(
                vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do,
                cua_hang.vi_do, cua_hang.kinh_do
            );
        }
    });

    // Sap xep theo khoang cach (gan nhat truoc)
    du_lieu_cua_hang.sort(function (a, b) {
        if (a.khoang_cach === null) return 1;
        if (b.khoang_cach === null) return -1;
        return a.khoang_cach - b.khoang_cach;
    });
}

/**
 * Them dau hieu cua hang vao ban do
 */
function them_dau_hieu_cua_hang() {
    du_lieu_cua_hang.forEach(function (cua_hang) {
        if (cua_hang.vi_do && cua_hang.kinh_do) {
            var mau_icon = cua_hang.co_su_kien ? 'orange' : 'blue';
            cua_hang.dau_hieu = L.marker([cua_hang.vi_do, cua_hang.kinh_do], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-' + mau_icon + '.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                })
            }).addTo(ban_do);

            var noi_dung_popup = '<b>' + cua_hang.ten + '</b><br>' +
                cua_hang.dia_chi + '<br>' +
                '<small>' + cua_hang.loai + '</small>';

            if (cua_hang.co_su_kien) {
                noi_dung_popup += '<br><strong style="color: #ffc107;">🎉 Có sự kiện!</strong>';
            }

            cua_hang.dau_hieu.bindPopup(noi_dung_popup);
        }
    });
}

/**
 * Hien thi danh sach cua hang trong sidebar
 * @param {string} id_bo_loc - ID cua select filter
 * @param {string} id_danh_sach - ID cua div hien thi danh sach
 */
function hien_thi_danh_sach_cua_hang(id_bo_loc, id_danh_sach) {
    var bo_loc_loai = document.getElementById(id_bo_loc).value;
    var bo_loc_ban_kinh = document.getElementById('radius-filter') ? document.getElementById('radius-filter').value : '';
    var noi_dung_danh_sach = document.getElementById(id_danh_sach);
    var html = '';

    var cua_hang_da_loc = du_lieu_cua_hang.filter(function (cua_hang) {
        // Loc theo loai
        if (bo_loc_loai && cua_hang.loai_id != bo_loc_loai) return false;

        // Loc theo ban kinh (neu co chon)
        if (bo_loc_ban_kinh && vi_tri_nguoi_dung) {
            var ban_kinh = parseFloat(bo_loc_ban_kinh);
            if (cua_hang.khoang_cach === null || cua_hang.khoang_cach > ban_kinh) {
                return false;
            }
        }

        return true;
    });

    // Cap nhat so luong cua hang tim thay
    if (vi_tri_nguoi_dung && bo_loc_ban_kinh) {
        document.getElementById('found-stores-count').textContent =
            'Tìm thấy ' + cua_hang_da_loc.length + ' cửa hàng trong bán kính ' + bo_loc_ban_kinh + ' km';
    } else if (vi_tri_nguoi_dung) {
        document.getElementById('found-stores-count').textContent =
            'Hiển thị tất cả ' + cua_hang_da_loc.length + ' cửa hàng';
    }

    if (cua_hang_da_loc.length === 0) {
        html = '<div class="loading">Không tìm thấy cửa hàng</div>';
    } else {
        cua_hang_da_loc.forEach(function (cua_hang) {
            var lop_css_su_kien = cua_hang.co_su_kien ? 'has-event' : '';
            var chu_khoang_cach = cua_hang.khoang_cach !== null ?
                (cua_hang.khoang_cach < 1 ?
                    (cua_hang.khoang_cach * 1000).toFixed(0) + ' m' :
                    cua_hang.khoang_cach.toFixed(2) + ' km') :
                'N/A';

            html += '<div class="store-item ' + lop_css_su_kien + '" onclick="chon_cua_hang(' + cua_hang.id + ')">';
            html += '<div class="store-name">' + cua_hang.ten + '</div>';
            html += '<div class="store-type">📍 ' + cua_hang.loai + '</div>';
            html += '<div class="store-distance">📏 Cách bạn: ' + chu_khoang_cach + '</div>';

            if (cua_hang.co_su_kien && cua_hang.danh_sach_su_kien.length > 0) {
                html += '<div class="store-events">';
                cua_hang.danh_sach_su_kien.forEach(function (su_kien) {
                    html += '<span class="event-badge">🎉 ' + su_kien + '</span>';
                });
                html += '</div>';
            }

            html += '</div>';
        });
    }

    noi_dung_danh_sach.innerHTML = html;
}

/**
 * Chon cua hang tu danh sach
 * @param {number} id_cua_hang - ID cua hang
 */
function chon_cua_hang(id_cua_hang) {
    var cua_hang = du_lieu_cua_hang.find(function (ch) { return ch.id === id_cua_hang; });
    if (cua_hang && cua_hang.dau_hieu) {
        ban_do.setView([cua_hang.vi_do, cua_hang.kinh_do], 16);
        cua_hang.dau_hieu.openPopup();

        // Dat lam diem den cho tim duong
        dat_diem_ket_thuc(cua_hang.vi_do, cua_hang.kinh_do);

        // AUTO-ROUTE: Neu da co vi tri nguoi dung, dat lam diem bat dau va tim duong luon
        if (vi_tri_nguoi_dung) {
            dat_diem_bat_dau(vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do);
            calculateRoute();
        }
    }
}


// ==================== CAC HAM TIM DUONG ====================

/**
 * Bat dau chon diem xuat phat
 */
function selectStart() {
    dang_chon_diem_bat_dau = true;
    dang_chon_diem_ket_thuc = false;
    ban_do.getContainer().style.cursor = 'crosshair';
}

/**
 * Bat dau chon diem ket thuc
 */
function selectEnd() {
    dang_chon_diem_ket_thuc = true;
    dang_chon_diem_bat_dau = false;
    ban_do.getContainer().style.cursor = 'crosshair';
}

/**
 * Dat diem bat dau cho tim duong
 * @param {number} vi_do - Vi do
 * @param {number} kinh_do - Kinh do
 */
function dat_diem_bat_dau(vi_do, kinh_do) {
    if (dau_hieu_bat_dau) ban_do.removeLayer(dau_hieu_bat_dau);

    dau_hieu_bat_dau = L.marker([vi_do, kinh_do], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(ban_do);
    dau_hieu_bat_dau.bindPopup("Điểm xuất phát");

    toa_do_bat_dau = [kinh_do, vi_do];
    document.getElementById('start-coords').textContent = vi_do.toFixed(5) + ', ' + kinh_do.toFixed(5);
}

/**
 * Dat diem ket thuc cho tim duong
 * @param {number} vi_do - Vi do
 * @param {number} kinh_do - Kinh do
 */
function dat_diem_ket_thuc(vi_do, kinh_do) {
    if (dau_hieu_ket_thuc) ban_do.removeLayer(dau_hieu_ket_thuc);

    dau_hieu_ket_thuc = L.marker([vi_do, kinh_do], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(ban_do);
    dau_hieu_ket_thuc.bindPopup("Điểm đến");

    toa_do_ket_thuc = [kinh_do, vi_do];
    document.getElementById('end-coords').textContent = vi_do.toFixed(5) + ', ' + kinh_do.toFixed(5);
}

/**
 * Tinh toan tuyen duong bang OSRM API
 */
function calculateRoute() {
    if (!toa_do_bat_dau || !toa_do_ket_thuc) {
        alert('Vui lòng chọn cả điểm xuất phát và điểm đến');
        return;
    }

    var url = `https://router.project-osrm.org/route/v1/driving/${toa_do_bat_dau[0]},${toa_do_bat_dau[1]};${toa_do_ket_thuc[0]},${toa_do_ket_thuc[1]}?overview=full&geometries=geojson`;

    fetch(url)
        .then(response => response.json())
        .then(du_lieu => {
            if (du_lieu.code === 'Ok') {
                var tuyen_duong = du_lieu.routes[0];
                var toa_do = tuyen_duong.geometry.coordinates.map(coord => [coord[1], coord[0]]);

                if (duong_di) ban_do.removeLayer(duong_di);

                duong_di = L.polyline(toa_do, {
                    color: 'blue',
                    weight: 5,
                    opacity: 0.7
                }).addTo(ban_do);

                ban_do.fitBounds(duong_di.getBounds());

                var khoang_cach = (tuyen_duong.distance / 1000).toFixed(2);
                var thoi_gian = Math.round(tuyen_duong.duration / 60);

                document.getElementById('distance').textContent = khoang_cach + ' km';
                document.getElementById('duration').textContent = thoi_gian + ' phút';
                document.getElementById('route-info').style.display = 'block';
            } else {
                alert('Không thể tìm được tuyến đường');
            }
        })
        .catch(loi => {
            console.error('Loi:', loi);
            alert('Lỗi khi tính toán đường đi');
        });
}

/**
 * Xoa tuyen duong va cac diem da chon
 */
function clearRoute() {
    if (dau_hieu_bat_dau) ban_do.removeLayer(dau_hieu_bat_dau);
    if (dau_hieu_ket_thuc) ban_do.removeLayer(dau_hieu_ket_thuc);
    if (duong_di) ban_do.removeLayer(duong_di);

    dau_hieu_bat_dau = null;
    dau_hieu_ket_thuc = null;
    duong_di = null;
    toa_do_bat_dau = null;
    toa_do_ket_thuc = null;

    document.getElementById('start-coords').textContent = 'Chưa chọn';
    document.getElementById('end-coords').textContent = 'Chưa chọn';
    document.getElementById('route-info').style.display = 'none';
    ban_do.getContainer().style.cursor = '';
}

/**
 * Loc cua hang (ham wrapper de goi tu HTML)
 */
function filterStores() {
    hien_thi_danh_sach_cua_hang('type-filter', 'store-list');
}
