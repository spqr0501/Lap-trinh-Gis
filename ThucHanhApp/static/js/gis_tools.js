/**
 * ============================================================================
 * CONG CU GIS - GIS TOOLS JAVASCRIPT LIBRARY
 * ============================================================================
 * Thu vien cac ham GIS tu viet cho ban do va tim duong
 * Custom GIS utility functions for mapping and routing
 * 
 * Phien ban: 2.0
 * Ngon ngu: JavaScript (ES5/ES6)
 * Thu vien phu thuoc: Leaflet.js
 */

// ============================================================================
// BIEN TOAN CUC - GLOBAL VARIABLES
// ============================================================================

var ban_do = null;                      // Leaflet map object
var du_lieu_cua_hang = [];              // Danh sach tat ca cua hang
var vi_tri_nguoi_dung = null;           // Vi tri hien tai cua nguoi dung
var dau_hieu_nguoi_dung = null;         // Marker vi tri nguoi dung

// Cac bien cho chuc nang tim duong
var dau_hieu_bat_dau = null;            // Marker diem xuat phat
var dau_hieu_ket_thuc = null;           // Marker diem dich den
var duong_di = null;                    // Polyline duong di
var dang_chon_diem_bat_dau = false;     // Flag chon diem bat dau
var dang_chon_diem_ket_thuc = false;    // Flag chon diem ket thuc
var toa_do_bat_dau = null;              // Toa do diem bat dau [lng, lat]
var toa_do_ket_thuc = null;             // Toa do diem ket thuc [lng, lat]
var vong_tron_ban_kinh = null;          // Vong tron vung dem ban kinh


// ============================================================================
// CAC HAM TINH TOAN GIS - GIS CALCULATION FUNCTIONS
// ============================================================================

/**
 * Tinh khoang cach giua 2 diem bang cong thuc Haversine
 * 
 * GIAI THICH:
 * - Cong thuc Haversine duoc su dung de tinh khoang cach giua 2 diem
 *   tren mat cau (trai dat) dua vao toa do kinh vi do
 * - Do chinh xac cao cho cac khoang cach < 1000km
 * - San so cua tinh toan so voi WGS84 ellipsoid < 0.5%
 * 
 * THAM SO:
 *   @param {number} vi_do_1 - Vi do diem 1 (do)
 *   @param {number} kinh_do_1 - Kinh do diem 1 (do)
 *   @param {number} vi_do_2 - Vi do diem 2 (do)
 *   @param {number} kinh_do_2 - Kinh do diem 2 (do)
 * 
 * TRA VE:
 *   @returns {number} Khoang cach theo don vi kilometers
 * 
 * VI DU:
 *   >>> var khoang_cach = tinh_khoang_cach(16.05, 108.20, 16.06, 108.21);
 *   >>> console.log(khoang_cach.toFixed(2) + " km");
 */
function tinh_khoang_cach(vi_do_1, kinh_do_1, vi_do_2, kinh_do_2) {
    var BAN_KINH_TRAI_DAT = 6371; // Ban kinh trai dat (km)

    // Chuyen doi tu do sang radian
    var d_vi_do = (vi_do_2 - vi_do_1) * Math.PI / 180;
    var d_kinh_do = (kinh_do_2 - kinh_do_1) * Math.PI / 180;

    // Cong thuc Haversine
    var a = Math.sin(d_vi_do / 2) * Math.sin(d_vi_do / 2) +
        Math.cos(vi_do_1 * Math.PI / 180) * Math.cos(vi_do_2 * Math.PI / 180) *
        Math.sin(d_kinh_do / 2) * Math.sin(d_kinh_do / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    var khoang_cach = BAN_KINH_TRAI_DAT * c;

    return khoang_cach;
}


/**
 * Tim vi tri nguoi dung (manual - khi bam nut)
 * 
 * GIAI THICH:
 * - Su dung Geolocation API cua trinh duyet
 * - Yeu cau quyen truy cap vi tri tu nguoi dung
 * - Hien thi marker tren ban do khi tim thay vi tri
 * - Tu dong set lam diem xuat phat cho tim duong
 * - Tinh khoang cach den tat ca cac cua hang
 * 
 * THAM SO:
 *   Khong co (su dung navigator.geolocation)
 * 
 * TRA VE:
 *   void - Cap nhat bien toan cuc vi_tri_nguoi_dung
 * 
 * VI DU:
 *   <button onclick="tim_vi_tri_nguoi_dung()">Tim Vi Tri</button>
 */
function tim_vi_tri_nguoi_dung() {
    if (!navigator.geolocation) {
        alert('Trình duyệt không hỗ trợ geolocation');
        return;
    }

    document.getElementById('user-coords').textContent = 'Đang tìm...';

    navigator.geolocation.getCurrentPosition(
        function (vi_tri) {
            // Luu vi tri vao bien toan cuc
            vi_tri_nguoi_dung = {
                vi_do: vi_tri.coords.latitude,
                kinh_do: vi_tri.coords.longitude
            };

            // Cap nhat UI
            document.getElementById('user-coords').textContent =
                vi_tri_nguoi_dung.vi_do.toFixed(5) + ', ' + vi_tri_nguoi_dung.kinh_do.toFixed(5);

            // Hien thi thong bao
            document.getElementById('user-location-info').style.display = 'block';

            // Them dau hieu nguoi dung (marker mau tim)
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


// ============================================================================
// CAC HAM BAN DO - MAP FUNCTIONS
// ============================================================================

/**
 * Khoi tao ban do Leaflet
 * 
 * GIAI THICH:
 * - Tao doi tuong Leaflet map
 * - Them tile layer (OpenStreetMap)
 * - Gan su kien click de chon diem cho tim duong
 * - Set view den toa do va zoom level chi dinh
 * 
 * THAM SO:
 *   @param {string} id_container - ID cua div container chua ban do
 *   @param {number} vi_do - Vi do trung tam ban do
 *   @param {number} kinh_do - Kinh do trung tam ban do
 *   @param {number} muc_zoom - Muc zoom (1-20, 13 la phu hop cho thanh pho)
 * 
 * TRA VE:
 *   @returns {L.Map} Doi tuong Leaflet map
 * 
 * VI DU:
 *   >>> var my_map = khoi_tao_ban_do('map', 16.0544, 108.2022, 13);
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
 * 
 * GIAI THICH:
 * - Duyet qua tung cua hang trong danh sach
 * - Tinh khoang cach tu vi tri nguoi dung den cua hang
 * - Sap xep danh sach theo khoang cach (gan nhat truoc)
 * - Cap nhat thuoc tinh khoang_cach cho moi cua hang
 * 
 * THAM SO:
 *   Khong co (su dung bien toan cuc vi_tri_nguoi_dung va du_lieu_cua_hang)
 * 
 * TRA VE:
 *   void - Cap nhat du_lieu_cua_hang.khoang_cach
 * 
 * VI DU:
 *   >>> tinh_khoang_cach_cac_cua_hang();
 *   >>> console.log("Gan nhat:", du_lieu_cua_hang[0].ten);
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
 * 
 * GIAI THICH:
 * - Tao marker cho moi cua hang co toa do
 * - Marker mau cam cho cua hang co su kien
 * - Marker mau xanh cho cua hang binh thuong
 * - Them popup voi thong tin cua hang
 * - Luu marker vao thuoc tinh cua hang de tai su dung
 * 
 * THAM SO:
 *   Khong co (su dung bien toan cuc du_lieu_cua_hang)
 * 
 * TRA VE:
 *   void - Them markers vao ban do
 * 
 * VI DU:
 *   >>> them_dau_hieu_cua_hang();
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

            noi_dung_popup +=
                '<br><div style="margin-top:8px; display:flex; gap:5px; flex-wrap:wrap;">' +
                '<button onclick="xem_danh_gia(' + cua_hang.id + ', \'' + cua_hang.ten.replace(/'/g, "\\'") + '\')" ' +
                'style="padding:4px 8px; font-size:0.8rem; background:#667eea; color:white; border:none; border-radius:4px; cursor:pointer;">⭐ Đánh Giá</button>' +
                '<button onclick="mo_form_danh_gia(' + cua_hang.id + ', \'' + cua_hang.ten.replace(/'/g, "\\'") + '\')" ' +
                'style="padding:4px 8px; font-size:0.8rem; background:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;">✏️ Viết Đánh Giá</button>' +
                '<a href="/dat-hang/' + cua_hang.id + '/" ' +
                'style="padding:4px 8px; font-size:0.8rem; background:#ff6b35; color:white; border:none; border-radius:4px; cursor:pointer; text-decoration:none;">🛒 Đặt Hàng</a>' +
                '</div>';

            cua_hang.dau_hieu.bindPopup(noi_dung_popup, { minWidth: 200 });
        }
    });
}


/**
 * Hien thi danh sach cua hang trong sidebar
 * 
 * GIAI THICH:
 * - Loc cua hang theo loai va ban kinh (neu co)
 * - Tao HTML cho moi cua hang trong danh sach
 * - Hien thi khoang cach tu nguoi dung (neu da biet vi tri)
 * - Highlight cua hang co su kien
 * - Cap nhat so luong cua hang tim thay
 * 
 * THAM SO:
 *   @param {string} id_bo_loc - ID cua select filter loai cua hang
 *   @param {string} id_danh_sach - ID cua div hien thi danh sach
 * 
 * TRA VE:
 *   void - Cap nhat innerHTML cua danh sach
 * 
 * VI DU:
 *   >>> hien_thi_danh_sach_cua_hang('type-filter', 'store-list');
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

    // Ve/xoa vong tron ban kinh tren ban do
    if (vong_tron_ban_kinh) {
        ban_do.removeLayer(vong_tron_ban_kinh);
        vong_tron_ban_kinh = null;
    }
    if (bo_loc_ban_kinh && vi_tri_nguoi_dung) {
        var ban_kinh_met = parseFloat(bo_loc_ban_kinh) * 1000;
        vong_tron_ban_kinh = L.circle(
            [vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do],
            {
                radius: ban_kinh_met,
                color: '#667eea',
                fillColor: '#667eea',
                fillOpacity: 0.1,
                weight: 2,
                dashArray: '5, 10'
            }
        ).addTo(ban_do);
    }

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

            html += '<button onclick="event.stopPropagation(); xem_danh_gia(' + cua_hang.id + ', \'' + cua_hang.ten.replace(/'/g, "\\'") + '\')" style="margin-top:6px; padding:4px 10px; font-size:0.8rem; background:#667eea; color:white; border:none; border-radius:4px; cursor:pointer;">⭐ Xem Đánh Giá</button>';
            html += '</div>';
        });
    }

    noi_dung_danh_sach.innerHTML = html;
}


/**
 * Chon cua hang tu danh sach hoac ban do
 * 
 * GIAI THICH:
 * - Tim cua hang theo ID
 * - Zoom ban do den vi tri cua hang
 * - Mo popup cua cua hang
 * - Tu dong set lam diem den cho tim duong
 * - Neu da co vi tri nguoi dung, tu dong tinh duong
 * 
 * THAM SO:
 *   @param {number} id_cua_hang - ID cua cua hang can chon
 * 
 * TRA VE:
 *   void - Cap nhat ban do va bat dau tim duong
 * 
 * VI DU:
 *   >>> chon_cua_hang(5);
 *   // Zoom den cua hang ID=5 va tim duong tu vi tri hien tai
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


// ============================================================================
// CAC HAM TIM DUONG - ROUTING FUNCTIONS
// ============================================================================

/**
 * Bat dau chon diem xuat phat
 * 
 * GIAI THICH:
 * - Doi con tro chuot thanh dau + (crosshair)
 * - Cho phep nguoi dung click tren ban do de chon diem bat dau
 * - Tat che do chon diem ket thuc
 * 
 * THAM SO:
 *   Khong co
 * 
 * TRA VE:
 *   void - Set flag dang_chon_diem_bat_dau = true
 * 
 * VI DU:
 *   <button onclick="selectStart()">Chon Diem Bat Dau</button>
 */
function selectStart() {
    dang_chon_diem_bat_dau = true;
    dang_chon_diem_ket_thuc = false;
    ban_do.getContainer().style.cursor = 'crosshair';
}


/**
 * Bat dau chon diem ket thuc
 * 
 * GIAI THICH:
 * - Doi con tro chuot thanh dau + (crosshair)
 * - Cho phep nguoi dung click tren ban do de chon diem ket thuc
 * - Tat che do chon diem bat dau
 * 
 * THAM SO:
 *   Khong co
 * 
 * TRA VE:
 *   void - Set flag dang_chon_diem_ket_thuc = true
 * 
 * VI DU:
 *   <button onclick="selectEnd()">Chon Diem Ket Thuc</button>
 */
function selectEnd() {
    dang_chon_diem_ket_thuc = true;
    dang_chon_diem_bat_dau = false;
    ban_do.getContainer().style.cursor = 'crosshair';
}


/**
 * Dat diem bat dau cho tim duong
 * 
 * GIAI THICH:
 * - Tao marker mau xanh la cho diem bat dau
 * - Luu toa do vao bien toan cuc
 * - Cap nhat hien thi toa do tren UI
 * - Xoa marker cu neu da co
 * 
 * THAM SO:
 *   @param {number} vi_do - Vi do diem bat dau
 *   @param {number} kinh_do - Kinh do diem bat dau
 * 
 * TRA VE:
 *   void - Tao marker va cap nhat bien toan cuc
 * 
 * VI DU:
 *   >>> dat_diem_bat_dau(16.0544, 108.2022);
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

    // Cap nhat vi tri nguoi dung theo diem xuat phat → tinh lai "Cach ban"
    vi_tri_nguoi_dung = { vi_do: vi_do, kinh_do: kinh_do };
    tinh_khoang_cach_cac_cua_hang();
    hien_thi_danh_sach_cua_hang('type-filter', 'store-list');
}


/**
 * Dat diem ket thuc cho tim duong
 * 
 * GIAI THICH:
 * - Tao marker mau do cho diem ket thuc
 * - Luu toa do vao bien toan cuc
 * - Cap nhat hien thi toa do tren UI
 * - Xoa marker cu neu da co
 * 
 * THAM SO:
 *   @param {number} vi_do - Vi do diem ket thuc
 *   @param {number} kinh_do - Kinh do diem ket thuc
 * 
 * TRA VE:
 *   void - Tao marker va cap nhat bien toan cuc
 * 
 * VI DU:
 *   >>> dat_diem_ket_thuc(16.0644, 108.2122);
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
 * 
 * GIAI THICH:
 * - Goi OSRM routing API (Project-OSRM.org)
 * - Nhan geometry tuyen duong dang GeoJSON
 * - Ve duong di len ban do (polyline mau xanh)
 * - Hien thi khoang cach va thoi gian di chuyen
 * - Tu dong zoom de hien thi toan bo tuyen duong
 * 
 * THAM SO:
 *   Khong co (su dung bien toan cuc toa_do_bat_dau, toa_do_ket_thuc)
 * 
 * TRA VE:
 *   void - Ve route len ban do va cap nhat UI
 * 
 * VI DU:
 *   >>> calculateRoute();
 *   // Tinh va ve duong di giua diem bat dau va ket thuc
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

                // Hien thi thong tin ngay tren duong di (giua tuyen duong)
                var so_diem = toa_do.length;
                var diem_giua = toa_do[Math.floor(so_diem / 2)];
                duong_di.bindTooltip(
                    '📏 ' + khoang_cach + ' km  ⏱️ ' + thoi_gian + ' phút',
                    {
                        permanent: true,
                        direction: 'center',
                        className: 'route-tooltip'
                    }
                ).openTooltip(diem_giua);

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
 * 
 * GIAI THICH:
 * - Xoa tat ca markers (diem bat dau, diem ket thuc)
 * - Xoa duong di (polyline)
 * - Reset tat ca bien toan cuc ve null
 * - An thong tin tuyen duong tren UI
 * - Doi con tro chuot ve binh thuong
 * 
 * THAM SO:
 *   Khong co
 * 
 * TRA VE:
 *   void - Xoa tat ca routing data
 * 
 * VI DU:
 *   <button onclick="clearRoute()">Xoa Duong Di</button>
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


// ============================================================================
// CAC HAM TIEN ICH - UTILITY FUNCTIONS
// ============================================================================

/**
 * Loc cua hang (ham wrapper de goi tu HTML)
 * 
 * GIAI THICH:
 * - Wrapper function de goi tu onchange cua select filter
 * - Goi lai ham hien_thi_danh_sach_cua_hang
 * - Cap nhat danh sach theo bo loc moi
 * 
 * THAM SO:
 *   Khong co
 * 
 * TRA VE:
 *   void - Cap nhat danh sach cua hang
 * 
 * VI DU:
 *   <select onchange="filterStores()">...</select>
 */
function filterStores() {
    hien_thi_danh_sach_cua_hang('type-filter', 'store-list');
}


// ============================================================================
// TIM KIEM DIA CHI - ADDRESS SEARCH (NOMINATIM GEOCODING)
// ============================================================================

// Bien toan cuc cho tim kiem
var dau_hieu_tim_kiem = null;    // Marker ket qua tim kiem

/**
 * Tim dia chi bang Nominatim API (OpenStreetMap Geocoding)
 * 
 * GIAI THICH:
 * - Su dung Nominatim API cua OpenStreetMap (mien phi)
 * - Nominatim chuyen doi dia chi text thanh toa do (geocoding)
 * - Hien thi danh sach ket qua de nguoi dung chon
 * - Uu tien ket qua tai Viet Nam (countrycodes=vn)
 * 
 * THAM SO:
 *   Khong co (lay gia tri tu input #search-address)
 * 
 * TRA VE:
 *   void - Hien thi danh sach ket qua tim kiem
 * 
 * VI DU:
 *   >>> tim_dia_chi();
 *   // Nhap "29 Hai Phong Da Nang" → hien thi ket qua
 */
function tim_dia_chi() {
    var dia_chi = document.getElementById('search-address').value.trim();
    if (!dia_chi) {
        alert('Vui lòng nhập địa chỉ cần tìm');
        return;
    }

    var ket_qua_div = document.getElementById('search-results');
    ket_qua_div.innerHTML = '<div class="loading">Đang tìm kiếm...</div>';

    // Goi Nominatim API
    var url = 'https://nominatim.openstreetmap.org/search?format=json&q=' +
        encodeURIComponent(dia_chi) +
        '&countrycodes=vn&limit=5&addressdetails=1';

    fetch(url, {
        headers: {
            'Accept-Language': 'vi'
        }
    })
        .then(function (response) { return response.json(); })
        .then(function (du_lieu) {
            if (du_lieu.length === 0) {
                ket_qua_div.innerHTML = '<div class="loading">Không tìm thấy địa chỉ</div>';
                return;
            }

            // Hien thi danh sach ket qua
            var html = '';
            du_lieu.forEach(function (ket_qua, chi_so) {
                html += '<div class="store-item" style="cursor:pointer; padding: 8px; margin: 3px 0; background: #f8f9fa; border-radius: 5px; border-left: 3px solid #667eea;" ' +
                    'onclick="chon_dia_chi(' + ket_qua.lat + ', ' + ket_qua.lon + ', \'' + ket_qua.display_name.replace(/'/g, "\\'") + '\')">' +
                    '<div style="font-size: 0.85rem;">' + ket_qua.display_name + '</div>' +
                    '</div>';
            });
            ket_qua_div.innerHTML = html;
        })
        .catch(function (loi) {
            console.error('Loi tim kiem:', loi);
            ket_qua_div.innerHTML = '<div class="loading">Lỗi khi tìm kiếm</div>';
        });
}


/**
 * Chon dia chi tu ket qua tim kiem
 * 
 * GIAI THICH:
 * - Di chuyen ban do den vi tri da chon
 * - Them marker do tai vi tri
 * - Hien thi popup voi ten dia chi
 * - Xoa marker tim kiem cu (neu co)
 * 
 * THAM SO:
 *   @param {number} vi_do - Vi do cua dia chi
 *   @param {number} kinh_do - Kinh do cua dia chi
 *   @param {string} ten_dia_chi - Ten hien thi cua dia chi
 * 
 * TRA VE:
 *   void - Di chuyen ban do va them marker
 * 
 * VI DU:
 *   >>> chon_dia_chi(16.0544, 108.2022, "29 Hai Phong, Da Nang");
 */
function chon_dia_chi(vi_do, kinh_do, ten_dia_chi) {
    // Xoa marker cu
    if (dau_hieu_tim_kiem) ban_do.removeLayer(dau_hieu_tim_kiem);

    // Di chuyen ban do
    ban_do.setView([vi_do, kinh_do], 16);

    // Them marker
    dau_hieu_tim_kiem = L.marker([vi_do, kinh_do], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(ban_do);
    dau_hieu_tim_kiem.bindPopup('<b>Kết quả tìm kiếm</b><br>' + ten_dia_chi).openPopup();

    // SET LAM DIEM XUAT PHAT ROUTING
    vi_tri_nguoi_dung = { vi_do: parseFloat(vi_do), kinh_do: parseFloat(kinh_do) };
    dat_diem_bat_dau(parseFloat(vi_do), parseFloat(kinh_do));

    // Tinh lai khoang cach den cac cua hang
    tinh_khoang_cach_cac_cua_hang();
    hien_thi_danh_sach_cua_hang('type-filter', 'store-list');

    // Cap nhat UI vi tri
    document.getElementById('user-coords').textContent =
        parseFloat(vi_do).toFixed(5) + ', ' + parseFloat(kinh_do).toFixed(5);
    document.getElementById('user-location-info').style.display = 'block';

    // Xoa ket qua tim kiem
    document.getElementById('search-results').innerHTML = '';
    document.getElementById('search-address').value = '';
}
// ============================================================================
// PANEL DANH GIA - REVIEW PANEL
// ============================================================================

function xem_danh_gia(cua_hang_id, ten_cua_hang) {
    // Mo panel
    document.getElementById('review-panel-title').textContent = '⭐ ' + ten_cua_hang;
    document.getElementById('review-panel-body').innerHTML = '<div class="loading">Đang tải đánh giá...</div>';
    document.getElementById('review-panel').classList.add('open');
    document.getElementById('overlay').classList.add('open');

    // Goi API lay danh gia
    fetch('/api/danh-gia/' + cua_hang_id + '/')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            var html = '';

            // Tong quan
            if (data.so_danh_gia === 0) {
                html = '<div class="review-empty">📝 Chưa có đánh giá nào</div>';
            } else {
                var sao_trung_binh = '';
                for (var i = 1; i <= 5; i++) {
                    sao_trung_binh += i <= Math.round(data.trung_binh) ? '★' : '☆';
                }
                html += '<div class="review-summary">';
                html += '<div class="review-avg">' + data.trung_binh + '</div>';
                html += '<div class="review-stars">' + sao_trung_binh + '</div>';
                html += '<div class="review-count">' + data.so_danh_gia + ' đánh giá</div>';
                html += '</div>';

                // Danh sach danh gia
                data.danh_gias.forEach(function (dg) {
                    var sao = '';
                    for (var i = 1; i <= 5; i++) {
                        sao += i <= dg.diem ? '★' : '☆';
                    }
                    html += '<div class="review-item">';
                    html += '<div class="review-item-header">';
                    html += '<span class="review-item-stars">' + sao + '</span>';
                    html += '<span class="review-item-date">' + dg.ngay + '</span>';
                    html += '</div>';
                    if (dg.nhan_xet) {
                        html += '<div class="review-item-text">' + dg.nhan_xet + '</div>';
                    }
                    html += '</div>';
                });
            }

            document.getElementById('review-panel-body').innerHTML = html;
        })
        .catch(function () {
            document.getElementById('review-panel-body').innerHTML = '<div class="review-empty">Lỗi khi tải đánh giá</div>';
        });
}

function dong_panel_danh_gia() {
    document.getElementById('review-panel').classList.remove('open');
    document.getElementById('overlay').classList.remove('open');
}


// Mo form viet danh gia trong panel ben phai
function mo_form_danh_gia(cua_hang_id, ten_cua_hang) {
    document.getElementById('review-panel-title').textContent = '✏️ Viết Đánh Giá - ' + ten_cua_hang;
    document.getElementById('review-panel').classList.add('open');
    document.getElementById('overlay').classList.add('open');

    var html = '<div style="padding: 0.5rem 0;">';

    // Chon so sao
    html += '<div style="margin-bottom: 1rem;">';
    html += '<label style="font-weight:bold; display:block; margin-bottom:6px;">Số sao:</label>';
    html += '<div id="sao-chon" style="font-size:2rem; color:#ccc; cursor:pointer;">';
    for (var i = 1; i <= 5; i++) {
        html += '<span data-sao="' + i + '" onclick="chon_sao(' + i + ')" onmouseover="hover_sao(' + i + ')" onmouseout="reset_sao()">☆</span>';
    }
    html += '</div>';
    html += '<input type="hidden" id="gia-tri-sao" value="0">';
    html += '</div>';

    // Nhap nhan xet
    html += '<div style="margin-bottom: 1rem;">';
    html += '<label style="font-weight:bold; display:block; margin-bottom:6px;">Nhận xét:</label>';
    html += '<textarea id="nhan-xet-input" rows="4" style="width:100%; padding:0.6rem; border:2px solid #e1e8ed; border-radius:5px; font-size:0.9rem; resize:vertical;" placeholder="Nhập nhận xét của bạn..."></textarea>';
    html += '</div>';

    // Nut gui
    html += '<button onclick="gui_danh_gia(' + cua_hang_id + ')" style="width:100%; padding:0.7rem; background:linear-gradient(135deg,#667eea,#764ba2); color:white; border:none; border-radius:5px; font-size:1rem; cursor:pointer; font-weight:bold;">Gửi Đánh Giá</button>';
    html += '<div id="thong-bao-danh-gia" style="margin-top:0.7rem; text-align:center;"></div>';

    html += '</div>';
    document.getElementById('review-panel-body').innerHTML = html;
}

// Tuong tac chon sao
function hover_sao(n) {
    var spans = document.querySelectorAll('#sao-chon span');
    spans.forEach(function (s, i) {
        s.textContent = i < n ? '★' : '☆';
        s.style.color = i < n ? '#f39c12' : '#ccc';
    });
}

function chon_sao(n) {
    document.getElementById('gia-tri-sao').value = n;
    hover_sao(n);
}

function reset_sao() {
    var gia_tri = parseInt(document.getElementById('gia-tri-sao').value);
    hover_sao(gia_tri);
}

// Gui danh gia len server
function gui_danh_gia(cua_hang_id) {
    var diem = parseInt(document.getElementById('gia-tri-sao').value);
    var nhan_xet = document.getElementById('nhan-xet-input').value.trim();
    var thong_bao = document.getElementById('thong-bao-danh-gia');

    if (diem < 1) {
        thong_bao.innerHTML = '<span style="color:red;">⚠️ Vui lòng chọn số sao!</span>';
        return;
    }

    thong_bao.innerHTML = '<span style="color:#667eea;">Đang gửi...</span>';

    fetch('/api/gui-danh-gia/' + cua_hang_id + '/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': lay_csrf_token() },
        body: JSON.stringify({ diem: diem, nhan_xet: nhan_xet })
    })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.thanh_cong) {
                thong_bao.innerHTML = '<span style="color:green;">✅ Cảm ơn bạn đã đánh giá!</span>';
                setTimeout(function () { dong_panel_danh_gia(); }, 1500);
            } else {
                thong_bao.innerHTML = '<span style="color:red;">❌ ' + (data.loi || 'Lỗi') + '</span>';
            }
        })
        .catch(function () {
            thong_bao.innerHTML = '<span style="color:red;">❌ Lỗi kết nối</span>';
        });
}

// Lay CSRF token tu cookie de gui POST request an toan
function lay_csrf_token() {
    var name = 'csrftoken';
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var c = cookies[i].trim();
        if (c.startsWith(name + '=')) return c.substring(name.length + 1);
    }
    return '';
}
