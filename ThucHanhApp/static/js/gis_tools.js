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
var cum_marker_cua_hang = null;         // Marker cluster group
var lop_nhiet = null;                   // Heatmap layer
var dang_bat_heatmap = false;           // Toggle heatmap state
var bo_chuyen_lop_ban_do = null;        // Control switcher OSM/Satellite/Dark
var chu_giai_ban_do = null;             // Legend control
var vong_highlight_cua_hang = null;     // Vòng tròn highlight cửa hàng (tìm kiếm)
var timer_goi_y_tim_cua_hang = null;    // Debounce autocomplete cửa hàng
var goi_y_tim_cua_hang_index = -1;      // Phím mũi tên trong danh sách gợi ý


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
            cap_nhat_goi_y_khuyen_mai();
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
    // Gioi han ban do trong pham vi Viet Nam
    var viet_nam_bounds = L.latLngBounds(
        L.latLng(8.18, 102.14),   // Goc Tay Nam
        L.latLng(23.39, 109.46)   // Goc Dong Bac
    );

    ban_do = L.map(id_container, {
        maxBounds: viet_nam_bounds.pad(0.1),
        minZoom: 5
    }).setView([vi_do, kinh_do], muc_zoom);

    var lop_osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    });
    var lop_ve_tinh = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        {
            attribution: 'Tiles &copy; Esri'
        }
    );
    var lop_toi = L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20
        }
    );
    lop_osm.addTo(ban_do);

    bo_chuyen_lop_ban_do = L.control.layers(
        {
            'OSM': lop_osm,
            'Satellite': lop_ve_tinh,
            'Dark mode': lop_toi
        },
        null,
        { position: 'topright', collapsed: false }
    ).addTo(ban_do);

    them_chu_giai_ban_do();

    // Fullscreen control
    if (L.control.fullscreen) {
        L.control.fullscreen({ position: 'topleft' }).addTo(ban_do);
    }

    // Scale bar (metric)
    L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(ban_do);

    // MiniMap (ban do tong quan goc duoi phai)
    if (L.Control.MiniMap) {
        var miniMapLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            minZoom: 0, maxZoom: 13
        });
        new L.Control.MiniMap(miniMapLayer, {
            toggleDisplay: true,
            minimized: false,
            position: 'bottomright'
        }).addTo(ban_do);
    }

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

    if (typeof L.markerClusterGroup === 'function') {
        cum_marker_cua_hang = L.markerClusterGroup({
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            maxClusterRadius: 50
        });
        ban_do.addLayer(cum_marker_cua_hang);
    }

    return ban_do;
}

function them_chu_giai_ban_do() {
    if (!ban_do || chu_giai_ban_do) return;
    chu_giai_ban_do = L.control({ position: 'bottomright' });
    chu_giai_ban_do.onAdd = function () {
        var div = L.DomUtil.create('div', 'map-legend');
        div.style.background = 'rgba(255,255,255,0.95)';
        div.style.padding = '8px 10px';
        div.style.borderRadius = '8px';
        div.style.boxShadow = '0 1px 6px rgba(0,0,0,0.25)';
        div.style.fontSize = '12px';
        div.style.lineHeight = '1.5';
        div.innerHTML =
            '<div style="font-weight:700; margin-bottom:4px;">Chú giải</div>' +
            '<div><span style="display:inline-block;width:10px;height:10px;background:#2b7bff;border-radius:50%;margin-right:6px;"></span>Cửa hàng thường</div>' +
            '<div><span style="display:inline-block;width:10px;height:10px;background:#ff9800;border-radius:50%;margin-right:6px;"></span>Cửa hàng có sự kiện</div>';
        L.DomEvent.disableClickPropagation(div);
        return div;
    };
    chu_giai_ban_do.addTo(ban_do);
}

function dinh_dang_thoi_gian_di_chuyen(so_giay) {
    var tong_giay = Math.max(0, Math.round(so_giay || 0));
    var gio = Math.floor(tong_giay / 3600);
    var phut = Math.round((tong_giay % 3600) / 60);
    if (phut === 60) {
        gio += 1;
        phut = 0;
    }

    if (gio > 0) {
        return phut > 0 ? (gio + ' giờ ' + phut + ' phút') : (gio + ' giờ');
    }
    if (phut <= 0 && tong_giay > 0) return '1 phút';
    return phut + ' phút';
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
function tao_noi_dung_popup_cua_hang(cua_hang) {
    var noi_dung_popup = '<b>' + cua_hang.ten + '</b><br>' +
        cua_hang.dia_chi + '<br>' +
        '<small>' + cua_hang.loai + '</small>';

    var khoang_cach_popup = '';
    if (vi_tri_nguoi_dung) {
        var kc = tinh_khoang_cach(
            vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do,
            cua_hang.vi_do, cua_hang.kinh_do
        );
        khoang_cach_popup = kc < 1 ? (kc * 1000).toFixed(0) + ' m' : kc.toFixed(2) + ' km';
    } else {
        khoang_cach_popup = 'Chưa xác định';
    }
    noi_dung_popup += '<br><small>📏 Cách bạn: <strong>' + khoang_cach_popup + '</strong></small>';

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
        'style="padding:4px 8px; font-size:0.8rem; background:#ff6b35; color:white; border:none; border-radius:4px; cursor:pointer; text-decoration:none;">🛍 Mua Ngay</a>' +
        '<button onclick="mo_modal_chon_mat_hang(' + cua_hang.id + ')" ' +
        'style="padding:4px 8px; font-size:0.8rem; background:#4fd1c5; color:white; border:none; border-radius:4px; cursor:pointer;">🛒 Thêm Vào Giỏ</button>' +
        '</div>';

    return noi_dung_popup;
}

function mo_modal_chon_mat_hang(cua_hang_id) {
    // Chuyen huong den trang mua hang/them vao gio cua cua hang do
    window.location.href = '/dat-hang/' + cua_hang_id + '/';
}

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
            });

            cua_hang.dau_hieu.bindPopup(tao_noi_dung_popup_cua_hang(cua_hang), { minWidth: 200 });
            cua_hang.dau_hieu.on('popupopen', function () {
                cua_hang.dau_hieu.setPopupContent(tao_noi_dung_popup_cua_hang(cua_hang));
            });

            if (cum_marker_cua_hang) {
                cum_marker_cua_hang.addLayer(cua_hang.dau_hieu);
            } else {
                cua_hang.dau_hieu.addTo(ban_do);
            }
        }
    });

    cap_nhat_lop_nhiet();
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
            html += ' <button class="btn-so-sanh" data-id="' + cua_hang.id + '" onclick="event.stopPropagation(); toggle_so_sanh(' + cua_hang.id + ')" style="margin-top:6px; padding:4px 10px; font-size:0.8rem; background:#667eea; color:white; border:none; border-radius:4px; cursor:pointer;">⚖️ So sánh</button>';
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
        if (cum_marker_cua_hang && typeof cum_marker_cua_hang.zoomToShowLayer === 'function') {
            cum_marker_cua_hang.zoomToShowLayer(cua_hang.dau_hieu, function () {
                cua_hang.dau_hieu.openPopup();
            });
        } else {
            cua_hang.dau_hieu.openPopup();
        }

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
// TIM CUA HANG - AUTOCOMPLETE + HIGHLIGHT
// ============================================================================

function chuan_hoa_tim_kiem_chuoi(s) {
    if (!s) return '';
    try {
        return String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
    } catch (e) {
        return String(s).toLowerCase().trim();
    }
}

function xoa_highlight_cua_hang() {
    if (vong_highlight_cua_hang && ban_do) {
        ban_do.removeLayer(vong_highlight_cua_hang);
        vong_highlight_cua_hang = null;
    }
}

function dat_vong_highlight_cua_hang(cua_hang) {
    xoa_highlight_cua_hang();
    if (!ban_do || !cua_hang || cua_hang.vi_do == null || cua_hang.kinh_do == null) return;
    vong_highlight_cua_hang = L.circle([cua_hang.vi_do, cua_hang.kinh_do], {
        radius: 200,
        color: '#d69e2e',
        fillColor: '#faf089',
        fillOpacity: 0.38,
        weight: 3,
        dashArray: '6, 8'
    }).addTo(ban_do);
}

function goi_y_tim_cua_hang() {
    if (timer_goi_y_tim_cua_hang) clearTimeout(timer_goi_y_tim_cua_hang);
    timer_goi_y_tim_cua_hang = setTimeout(function () {
        timer_goi_y_tim_cua_hang = null;
        hien_thi_goi_y_tim_cua_hang();
    }, 220);
}

function hien_thi_goi_y_tim_cua_hang() {
    var input = document.getElementById('search-store');
    var listEl = document.getElementById('store-autocomplete-list');
    if (!input || !listEl) return;

    var q = chuan_hoa_tim_kiem_chuoi(input.value);
    goi_y_tim_cua_hang_index = -1;

    if (q.length < 1) {
        listEl.style.display = 'none';
        listEl.innerHTML = '';
        xoa_highlight_cua_hang();
        return;
    }

    var ket_qua = [];
    du_lieu_cua_hang.forEach(function (ch) {
        if (!ch.ten && !ch.dia_chi) return;
        var ten = chuan_hoa_tim_kiem_chuoi(ch.ten);
        var dc = chuan_hoa_tim_kiem_chuoi(ch.dia_chi);
        var loai = chuan_hoa_tim_kiem_chuoi(ch.loai || '');
        if (ten.indexOf(q) !== -1 || dc.indexOf(q) !== -1 || loai.indexOf(q) !== -1) {
            ket_qua.push(ch);
        }
    });

    ket_qua = ket_qua.slice(0, 10);

    if (ket_qua.length === 0) {
        listEl.innerHTML = '<div class="store-autocomplete-item" style="cursor:default;color:#718096;">Không tìm thấy cửa hàng phù hợp</div>';
        listEl.style.display = 'block';
        return;
    }

    var html = '';
    ket_qua.forEach(function (ch) {
        html += '<div class="store-autocomplete-item" data-id="' + ch.id + '" ' +
            'onmousedown="event.preventDefault(); chon_tu_goi_y_tim_cua_hang(' + ch.id + ')">' +
            '<div class="ac-name">' + (ch.ten || '') + '</div>' +
            '<div class="ac-addr">' + (ch.dia_chi || '') + '</div>' +
            '</div>';
    });
    listEl.innerHTML = html;
    listEl.style.display = 'block';
}

function chon_tu_goi_y_tim_cua_hang(id_cua_hang) {
    var listEl = document.getElementById('store-autocomplete-list');
    var input = document.getElementById('search-store');
    if (listEl) {
        listEl.style.display = 'none';
        listEl.innerHTML = '';
    }
    var ch = du_lieu_cua_hang.find(function (c) { return c.id === id_cua_hang; });
    if (ch && input) {
        input.value = ch.ten || '';
    }
    chon_cua_hang(id_cua_hang);
    if (ch) {
        dat_vong_highlight_cua_hang(ch);
    }
}

function an_goi_y_tim_cua_hang_sau() {
    setTimeout(function () {
        var listEl = document.getElementById('store-autocomplete-list');
        if (listEl) listEl.style.display = 'none';
    }, 200);
}

function phim_tim_cua_hang(ev) {
    var listEl = document.getElementById('store-autocomplete-list');
    if (!listEl || listEl.style.display === 'none') return;

    var items = listEl.querySelectorAll('.store-autocomplete-item[data-id]');
    if (!items.length) return;

    if (ev.key === 'ArrowDown') {
        ev.preventDefault();
        goi_y_tim_cua_hang_index = Math.min(goi_y_tim_cua_hang_index + 1, items.length - 1);
        cap_nhat_active_goi_y(items);
    } else if (ev.key === 'ArrowUp') {
        ev.preventDefault();
        goi_y_tim_cua_hang_index = Math.max(goi_y_tim_cua_hang_index - 1, 0);
        cap_nhat_active_goi_y(items);
    } else if (ev.key === 'Enter') {
        if (goi_y_tim_cua_hang_index >= 0 && items[goi_y_tim_cua_hang_index]) {
            ev.preventDefault();
            var id = parseInt(items[goi_y_tim_cua_hang_index].getAttribute('data-id'), 10);
            if (!isNaN(id)) chon_tu_goi_y_tim_cua_hang(id);
        }
    } else if (ev.key === 'Escape') {
        listEl.style.display = 'none';
    }
}

function cap_nhat_active_goi_y(items) {
    for (var i = 0; i < items.length; i++) {
        items[i].classList.toggle('active', i === goi_y_tim_cua_hang_index);
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
    cap_nhat_goi_y_khuyen_mai();
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

    // Tao danh sach toa do cho OSRM (bat dau + waypoints + ket thuc)
    // Neu khoang cach lon (> 300km), them waypoints doc theo Viet Nam de route khong di qua nuoc khac
    var coords_str = toa_do_bat_dau[0] + ',' + toa_do_bat_dau[1];

    var lat_start = toa_do_bat_dau[1];
    var lat_end = toa_do_ket_thuc[1];
    var kc = Math.abs(lat_start - lat_end);

    if (kc > 3) {
        // Waypoints doc theo QL1A Viet Nam (kinh do ~106-108)
        var waypoints_vn = [
            [106.68, 10.78],   // TPHCM
            [106.60, 11.95],   // Binh Duong
            [107.60, 12.25],   // Dak Lak
            [108.05, 12.68],   // Ninh Thuan
            [108.23, 13.77],   // Binh Dinh
            [108.22, 14.47],   // Quang Ngai
            [108.22, 15.88],   // Da Nang
            [107.59, 16.46],   // Hue
            [106.60, 16.85],   // Quang Tri
            [106.32, 17.47],   // Quang Binh
            [106.27, 18.67],   // Nghe An - Vinh
            [105.78, 19.80],   // Thanh Hoa
            [105.85, 20.94],   // Ninh Binh
            [105.85, 21.03],   // Ha Noi
        ];

        // Loc waypoints nam giua 2 diem (theo lat)
        var lat_min = Math.min(lat_start, lat_end);
        var lat_max = Math.max(lat_start, lat_end);

        var wp_filtered = waypoints_vn.filter(function (wp) {
            return wp[1] > lat_min + 0.5 && wp[1] < lat_max - 0.5;
        });

        // Sap xep waypoints theo huong di
        if (lat_start > lat_end) {
            wp_filtered.sort(function (a, b) { return b[1] - a[1]; });
        } else {
            wp_filtered.sort(function (a, b) { return a[1] - b[1]; });
        }

        for (var i = 0; i < wp_filtered.length; i++) {
            coords_str += ';' + wp_filtered[i][0] + ',' + wp_filtered[i][1];
        }
    }

    coords_str += ';' + toa_do_ket_thuc[0] + ',' + toa_do_ket_thuc[1];

    var url = 'https://router.project-osrm.org/route/v1/driving/' + coords_str + '?overview=full&geometries=geojson';

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
                var thoi_gian_text = dinh_dang_thoi_gian_di_chuyen(tuyen_duong.duration);

                // Hien thi thong tin ngay tren duong di (giua tuyen duong)
                var so_diem = toa_do.length;
                var diem_giua = toa_do[Math.floor(so_diem / 2)];
                duong_di.bindTooltip(
                    '📏 ' + khoang_cach + ' km  ⏱️ ' + thoi_gian_text,
                    {
                        permanent: true,
                        direction: 'center',
                        className: 'route-tooltip'
                    }
                ).openTooltip(diem_giua);

                document.getElementById('distance').textContent = khoang_cach + ' km';
                document.getElementById('duration').textContent = thoi_gian_text;
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
    cap_nhat_goi_y_khuyen_mai();
}

function tim_cua_hang_gan_nhat() {
    var diem_moc = null;
    if (vi_tri_nguoi_dung) {
        diem_moc = { vi_do: vi_tri_nguoi_dung.vi_do, kinh_do: vi_tri_nguoi_dung.kinh_do };
    } else if (toa_do_bat_dau) {
        diem_moc = { vi_do: toa_do_bat_dau[1], kinh_do: toa_do_bat_dau[0] };
    }
    if (!diem_moc) {
        alert('Vui lòng chọn vị trí của bạn hoặc điểm xuất phát trước.');
        return;
    }

    var gan_nhat = null;
    var kc_nho_nhat = Number.MAX_VALUE;
    du_lieu_cua_hang.forEach(function (ch) {
        if (ch.vi_do == null || ch.kinh_do == null) return;
        var kc = tinh_khoang_cach(diem_moc.vi_do, diem_moc.kinh_do, ch.vi_do, ch.kinh_do);
        if (kc < kc_nho_nhat) {
            kc_nho_nhat = kc;
            gan_nhat = ch;
        }
    });

    if (!gan_nhat) {
        alert('Không tìm thấy cửa hàng có tọa độ hợp lệ.');
        return;
    }

    chon_cua_hang(gan_nhat.id);
}

function cap_nhat_lop_nhiet() {
    if (!ban_do || typeof L.heatLayer !== 'function') return;

    var points = [];
    du_lieu_cua_hang.forEach(function (ch) {
        if (ch.vi_do == null || ch.kinh_do == null) return;
        var weight = 0.2 + Math.min(1, ((ch.so_don_thanh_toan || 0) * 0.06 + (ch.so_danh_gia || 0) * 0.04));
        points.push([ch.vi_do, ch.kinh_do, weight]);
    });

    if (lop_nhiet) {
        ban_do.removeLayer(lop_nhiet);
        lop_nhiet = null;
    }
    lop_nhiet = L.heatLayer(points, {
        radius: 26,
        blur: 18,
        maxZoom: 17,
        minOpacity: 0.35
    });
    if (dang_bat_heatmap) lop_nhiet.addTo(ban_do);
}

function toggle_heatmap() {
    dang_bat_heatmap = !dang_bat_heatmap;
    if (!lop_nhiet) cap_nhat_lop_nhiet();
    if (!lop_nhiet) return;
    if (dang_bat_heatmap) {
        lop_nhiet.addTo(ban_do);
    } else {
        ban_do.removeLayer(lop_nhiet);
    }
}

function cap_nhat_goi_y_khuyen_mai() {
    var box = document.getElementById('promo-suggestions');
    if (!box) return;
    if (!vi_tri_nguoi_dung) {
        box.innerHTML = '<em>Hãy xác định vị trí để nhận gợi ý khuyến mãi gần bạn.</em>';
        return;
    }
    var radiusSelect = document.getElementById('promo-radius');
    var radiusKm = radiusSelect ? parseFloat(radiusSelect.value || '2') : 2;

    var goiY = [];
    du_lieu_cua_hang.forEach(function (ch) {
        if (!ch.co_su_kien || !ch.danh_sach_su_kien || ch.danh_sach_su_kien.length === 0) return;
        if (ch.vi_do == null || ch.kinh_do == null) return;
        var kc = tinh_khoang_cach(vi_tri_nguoi_dung.vi_do, vi_tri_nguoi_dung.kinh_do, ch.vi_do, ch.kinh_do);
        if (kc <= radiusKm) {
            goiY.push({
                ten: ch.ten,
                su_kien: ch.danh_sach_su_kien[0],
                kc: kc
            });
        }
    });
    goiY.sort(function (a, b) { return a.kc - b.kc; });

    if (goiY.length === 0) {
        box.innerHTML = 'Không có khuyến mãi trong bán kính đã chọn.';
        return;
    }
    var html = '<strong>🎁 Gợi ý gần bạn:</strong>';
    goiY.slice(0, 3).forEach(function (g) {
        html += '<div style="margin-top:4px;">' + g.ten + ' - ' + g.su_kien + ' (' + (g.kc < 1 ? (g.kc * 1000).toFixed(0) + 'm' : g.kc.toFixed(2) + 'km') + ')</div>';
    });
    box.innerHTML = html;
}


// ============================================================================
// TIM KIEM DIA CHI - ADDRESS SEARCH (NOMINATIM GEOCODING)
// ============================================================================

// Bien toan cuc cho tim kiem
var dau_hieu_tim_kiem = null;    // Marker ket qua tim kiem

// ============================================================================
// LICH SU TIM KIEM (localStorage) - dùng để hiển thị ở trang "Đơn hàng của tôi"
// ============================================================================
var SEARCH_HISTORY_KEY = 'webgis_search_history';
var SEARCH_HISTORY_PENDING_KEY = 'webgis_pending_search_selection';
var SEARCH_RECENT_SELECTED_KEY = 'webgis_recent_selected_search';

function historyKey(base) {
    var key = (window.WEBGIS_HISTORY_USER_KEY || 'guest').toString();
    return base + '_' + key;
}

function cap_nhat_lich_su_tim_kiem(ten_dia_chi, vi_do, kinh_do) {
    try {
        var storage = window.localStorage;
        var items = [];

        try {
            items = JSON.parse(storage.getItem(historyKey(SEARCH_HISTORY_KEY)) || '[]');
            if (!Array.isArray(items)) items = [];
        } catch (e) {
            items = [];
        }

        var normalized = (ten_dia_chi || '').trim();
        if (!normalized) return;

        // Loai trung theo dia chi da chon, dong thoi giu trang thai yeu thich neu co
        var yeu_thich = false;
        items = items.filter(function (it) {
            if (it && it.dia_chi === normalized) {
                yeu_thich = !!it.yeu_thich;
                return false;
            }
            return true;
        });

        items.unshift({
            dia_chi: normalized,
            vi_do: parseFloat(vi_do),
            kinh_do: parseFloat(kinh_do),
            ngay: new Date().toISOString(),
            yeu_thich: yeu_thich
        });
        items = items.slice(0, 10);

        storage.setItem(historyKey(SEARCH_HISTORY_KEY), JSON.stringify(items));

        // Luu dia chi da chon gan nhat de mo lai nhanh
        storage.setItem(historyKey(SEARCH_RECENT_SELECTED_KEY), JSON.stringify({
            dia_chi: normalized,
            vi_do: parseFloat(vi_do),
            kinh_do: parseFloat(kinh_do),
            ngay: new Date().toISOString()
        }));
    } catch (e) {
        // localStorage không khả dụng -> bỏ qua
    }
}

function ap_dung_tim_kiem_tu_lich_su_neu_co() {
    try {
        var pendingRaw = window.localStorage.getItem(historyKey(SEARCH_HISTORY_PENDING_KEY));
        if (!pendingRaw) return;
        window.localStorage.removeItem(historyKey(SEARCH_HISTORY_PENDING_KEY));

        var pending = JSON.parse(pendingRaw);
        if (!pending || pending.vi_do == null || pending.kinh_do == null) return;

        chon_dia_chi(pending.vi_do, pending.kinh_do, pending.dia_chi || 'Địa chỉ đã lưu');
    } catch (e) {
        // Bỏ qua nếu dữ liệu pending lỗi
    }
}

function xoa_lich_su_tim_kiem_khong_hop_le() {
    try {
        var items = JSON.parse(window.localStorage.getItem(historyKey(SEARCH_HISTORY_KEY)) || '[]');
        if (!Array.isArray(items)) {
            window.localStorage.setItem(historyKey(SEARCH_HISTORY_KEY), JSON.stringify([]));
            return;
        }
        items = items.filter(function (it) {
            return it && it.dia_chi;
        });
        window.localStorage.setItem(historyKey(SEARCH_HISTORY_KEY), JSON.stringify(items));
    } catch (e) {
        window.localStorage.setItem(historyKey(SEARCH_HISTORY_KEY), JSON.stringify([]));
    }
}

function hien_thi_dia_chi_gan_nhat() {
    var box = document.getElementById('recent-selected-search');
    if (!box) return;
    try {
        var raw = window.localStorage.getItem(historyKey(SEARCH_RECENT_SELECTED_KEY));
        if (!raw) {
            box.style.display = 'none';
            box.innerHTML = '';
            return;
        }
        var item = JSON.parse(raw);
        if (!item || item.vi_do == null || item.kinh_do == null || !item.dia_chi) {
            box.style.display = 'none';
            box.innerHTML = '';
            return;
        }
        box.style.display = 'block';
        box.innerHTML =
            '<div style="margin-top:8px; padding:8px; border-radius:6px; background:#edf2ff; border-left:3px solid #667eea;">' +
            '<div style="font-size:0.8rem; color:#555; margin-bottom:4px;">Địa chỉ đã chọn gần nhất</div>' +
            '<div style="font-size:0.85rem; color:#333; margin-bottom:6px;">' + item.dia_chi + '</div>' +
            '<button class="btn btn-primary btn-sm" onclick="chon_dia_chi(' + item.vi_do + ',' + item.kinh_do + ', \'' + item.dia_chi.replace(/'/g, "\\'") + '\')">Dùng lại</button>' +
            '</div>';
    } catch (e) {
        box.style.display = 'none';
        box.innerHTML = '';
    }
}

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
    // Chi luu lich su khi nguoi dung CHON ket qua cu the
    cap_nhat_lich_su_tim_kiem(ten_dia_chi, vi_do, kinh_do);

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

    // Cap nhat box dia chi gan nhat
    hien_thi_dia_chi_gan_nhat();
    cap_nhat_goi_y_khuyen_mai();
}
// ============================================================================
// PANEL DANH GIA - REVIEW PANEL
// ============================================================================
var review_panel_state = {
    cua_hang_id: null,
    ten_cua_hang: '',
    data: null,
    sao_loc: 0,
    xoa_anh_ids: [],
    anh_hien_tai: []
};

function sort_danh_gia_theo_like(ds) {
    return (ds || []).slice().sort(function (a, b) {
        var likeA = a.so_like || 0;
        var likeB = b.so_like || 0;
        if (likeB !== likeA) return likeB - likeA;
        return (b.id || 0) - (a.id || 0);
    });
}

function render_review_panel_body(data) {
    var html = '';
    if (!data || data.so_danh_gia === 0) {
        document.getElementById('review-panel-body').innerHTML = '<div class="review-empty">📝 Chưa có đánh giá nào</div>';
        return;
    }

    var sao_trung_binh = '';
    for (var i = 1; i <= 5; i++) {
        sao_trung_binh += i <= Math.round(data.trung_binh) ? '★' : '☆';
    }
    html += '<div class="review-summary">';
    html += '<div class="review-avg">' + data.trung_binh + '</div>';
    html += '<div class="review-stars">' + sao_trung_binh + '</div>';
    html += '<div class="review-count">' + data.so_danh_gia + ' đánh giá</div>';
    html += '</div>';

    if (data.phan_bo_sao) {
        html += '<div style="margin-bottom:10px;">';
        html += '<strong>Phân bố sao:</strong>';
        for (var s = 5; s >= 1; s--) {
            var count = data.phan_bo_sao[s] || 0;
            html += '<div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#555;">';
            html += '<span>' + s + ' sao</span><span>' + count + '</span>';
            html += '</div>';
        }
        html += '</div>';
    }

    html += '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px;">';
    html += '<button onclick="loc_danh_gia_theo_sao(0)" class="btn btn-sm" style="background:' + (review_panel_state.sao_loc === 0 ? '#dbe7ff' : '#edf2f7') + ';">Tất cả</button>';
    for (var f = 5; f >= 1; f--) {
        html += '<button onclick="loc_danh_gia_theo_sao(' + f + ')" class="btn btn-sm" style="background:' + (review_panel_state.sao_loc === f ? '#dbe7ff' : '#edf2f7') + ';">' + f + ' sao</button>';
    }
    html += '</div>';
    html += '<div id="danh-sach-danh-gia">';

    var ds = sort_danh_gia_theo_like(data.danh_gias);
    ds.forEach(function (dg) {
        if (review_panel_state.sao_loc && dg.diem !== review_panel_state.sao_loc) return;
        var sao = '';
        for (var i = 1; i <= 5; i++) {
            sao += i <= dg.diem ? '★' : '☆';
        }
        html += '<div class="review-item">';
        html += '<div class="review-item-header">';
        html += '<span class="review-item-stars">' + sao + '</span>';
        html += '<div style="text-align:right;">';
        html += '<div class="review-item-date">' + dg.ngay + '</div>';
        html += '<div class="review-item-user">👤 ' + (dg.ten_nguoi || 'Ẩn danh') + '</div>';
        html += '</div>';
        html += '</div>';
        if (dg.nhan_xet) html += '<div class="review-item-text">' + dg.nhan_xet + '</div>';
        if (dg.hinh_anhs && dg.hinh_anhs.length) {
            html += '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">';
            dg.hinh_anhs.forEach(function (url) {
                html += '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' +
                    '<img src="' + url + '" alt="Ảnh đánh giá" style="width:72px; height:72px; object-fit:cover; border-radius:6px; border:1px solid #e2e8f0;" />' +
                    '</a>';
            });
            html += '</div>';
        }
        html += '<div style="margin-top:6px; display:flex; align-items:center; gap:6px;">';
        html += '<button class="btn btn-sm" style="background:' + (dg.da_like ? '#c6f6d5' : '#edf2f7') + '; color:#2d3748;" onclick="toggle_like_danh_gia(' + dg.id + ')">👍 ' + (dg.da_like ? 'Đã like' : 'Like') + '</button>';
        html += '<span class="so-like" style="font-size:0.85rem; color:#555;">' + (dg.so_like || 0) + ' like</span>';
        html += '</div>';
        html += '</div>';
    });

    html += '</div>';
    document.getElementById('review-panel-body').innerHTML = html;
}

function xem_danh_gia(cua_hang_id, ten_cua_hang) {
    // Mo panel
    document.getElementById('review-panel-title').textContent = '⭐ ' + ten_cua_hang;
    document.getElementById('review-panel-body').innerHTML = '<div class="loading">Đang tải đánh giá...</div>';
    document.getElementById('review-panel').classList.add('open');
    document.getElementById('overlay').classList.add('open');
    review_panel_state.cua_hang_id = cua_hang_id;
    review_panel_state.ten_cua_hang = ten_cua_hang;
    review_panel_state.sao_loc = 0;

    // Goi API lay danh gia
    fetch('/api/danh-gia/' + cua_hang_id + '/')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            review_panel_state.data = data;
            render_review_panel_body(data);
        })
        .catch(function () {
            document.getElementById('review-panel-body').innerHTML = '<div class="review-empty">Lỗi khi tải đánh giá</div>';
        });
}

function loc_danh_gia_theo_sao(sao) {
    review_panel_state.sao_loc = sao || 0;
    if (review_panel_state.data) render_review_panel_body(review_panel_state.data);
}

function toggle_like_danh_gia(danh_gia_id) {
    fetch('/api/like-danh-gia/' + danh_gia_id + '/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': lay_csrf_token() }
    })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (!data.thanh_cong) {
                alert(data.loi || 'Không thể like đánh giá');
                return;
            }
            if (review_panel_state.data && review_panel_state.data.danh_gias) {
                review_panel_state.data.danh_gias = review_panel_state.data.danh_gias.map(function (dg) {
                    if (dg.id === danh_gia_id) {
                        dg.so_like = data.so_like || 0;
                        dg.da_like = !!data.da_like;
                    }
                    return dg;
                });
                render_review_panel_body(review_panel_state.data);
            }
        })
        .catch(function () {
            alert('Bạn cần đăng nhập để like đánh giá.');
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
    document.getElementById('review-panel-body').innerHTML = '<div class="loading">Đang tải form đánh giá...</div>';
    fetch('/api/danh-gia/' + cua_hang_id + '/')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            var danhGiaCuaToi = null;
            if (data && data.danh_gias) {
                data.danh_gias.forEach(function (dg) {
                    if (dg.la_cua_toi) danhGiaCuaToi = dg;
                });
            }
            review_panel_state.xoa_anh_ids = [];
            review_panel_state.anh_hien_tai = (danhGiaCuaToi && danhGiaCuaToi.hinh_anhs_obj) ? danhGiaCuaToi.hinh_anhs_obj.slice() : [];

            var html = '<div style="padding: 0.5rem 0;">';

            html += '<div style="margin-bottom: 1rem;">';
            html += '<label style="font-weight:bold; display:block; margin-bottom:6px;">Số sao:</label>';
            html += '<div id="sao-chon" style="font-size:2rem; color:#ccc; cursor:pointer;">';
            for (var i = 1; i <= 5; i++) {
                html += '<span data-sao="' + i + '" onclick="chon_sao(' + i + ')" onmouseover="hover_sao(' + i + ')" onmouseout="reset_sao()">☆</span>';
            }
            html += '</div>';
            html += '<input type="hidden" id="gia-tri-sao" value="' + (danhGiaCuaToi ? danhGiaCuaToi.diem : 0) + '">';
            html += '</div>';

            html += '<div style="margin-bottom: 1rem;">';
            html += '<label style="font-weight:bold; display:block; margin-bottom:6px;">Nhận xét:</label>';
            html += '<textarea id="nhan-xet-input" rows="4" style="width:100%; padding:0.6rem; border:2px solid #e1e8ed; border-radius:5px; font-size:0.9rem; resize:vertical;" placeholder="Nhập nhận xét của bạn...">' +
                (danhGiaCuaToi && danhGiaCuaToi.nhan_xet ? danhGiaCuaToi.nhan_xet : '') + '</textarea>';
            html += '</div>';

            html += '<div style="margin-bottom: 1rem;">';
            html += '<label style="font-weight:bold; display:block; margin-bottom:6px;">Ảnh hiện có:</label>';
            html += '<div id="anh-danh-gia-hien-co" style="display:flex; gap:6px; flex-wrap:wrap;"></div>';
            html += '</div>';

            html += '<div style="margin-bottom: 1rem;">';
            html += '<label style="font-weight:bold; display:block; margin-bottom:6px;">Thêm ảnh mới (tối đa tổng 3 ảnh):</label>';
            html += '<input type="file" id="hinh-anh-danh-gia" accept="image/*" multiple onchange="preview_anh_danh_gia(this)">';
            html += '<div id="anh-danh-gia-preview" style="display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;"></div>';
            html += '</div>';

            html += '<button onclick="gui_danh_gia(' + cua_hang_id + ')" style="width:100%; padding:0.7rem; background:linear-gradient(135deg,#667eea,#764ba2); color:white; border:none; border-radius:5px; font-size:1rem; cursor:pointer; font-weight:bold;">Gửi Đánh Giá</button>';
            html += '<div id="thong-bao-danh-gia" style="margin-top:0.7rem; text-align:center;"></div>';
            html += '</div>';
            document.getElementById('review-panel-body').innerHTML = html;
            render_anh_danh_gia_hien_co();
            reset_sao();
        })
        .catch(function () {
            document.getElementById('review-panel-body').innerHTML = '<div class="review-empty">Không tải được form đánh giá</div>';
        });
}

function render_anh_danh_gia_hien_co() {
    var box = document.getElementById('anh-danh-gia-hien-co');
    if (!box) return;
    box.innerHTML = '';
    if (!review_panel_state.anh_hien_tai || review_panel_state.anh_hien_tai.length === 0) {
        box.innerHTML = '<em style="color:#718096;">Chưa có ảnh.</em>';
        return;
    }
    review_panel_state.anh_hien_tai.forEach(function (anh) {
        if (review_panel_state.xoa_anh_ids.indexOf(anh.id) !== -1) return;
        box.innerHTML += '<div style="position:relative;">' +
            '<img src="' + anh.url + '" alt="Ảnh cũ" style="width:72px;height:72px;object-fit:cover;border:1px solid #e2e8f0;border-radius:6px;">' +
            '<button type="button" onclick="xoa_anh_cu_danh_gia(' + anh.id + ')" style="position:absolute;top:-6px;right:-6px;background:#e53e3e;color:#fff;border:none;border-radius:999px;width:20px;height:20px;line-height:20px;cursor:pointer;">×</button>' +
            '</div>';
    });
}

function xoa_anh_cu_danh_gia(anhId) {
    if (review_panel_state.xoa_anh_ids.indexOf(anhId) === -1) {
        review_panel_state.xoa_anh_ids.push(anhId);
    }
    render_anh_danh_gia_hien_co();
}

function preview_anh_danh_gia(input) {
    var box = document.getElementById('anh-danh-gia-preview');
    if (!box) return;
    box.innerHTML = '';
    var files = Array.prototype.slice.call(input.files || []);
    var soAnhConLai = (review_panel_state.anh_hien_tai || []).filter(function (anh) {
        return review_panel_state.xoa_anh_ids.indexOf(anh.id) === -1;
    }).length;
    if (soAnhConLai + files.length > 3) {
        alert('Tổng số ảnh sau cập nhật không được vượt quá 3.');
        input.value = '';
        return;
    }
    files.forEach(function (file) {
        var url = URL.createObjectURL(file);
        var img = document.createElement('img');
        img.src = url;
        img.style.width = '72px';
        img.style.height = '72px';
        img.style.objectFit = 'cover';
        img.style.border = '1px solid #e2e8f0';
        img.style.borderRadius = '6px';
        box.appendChild(img);
    });
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

    var filesInput = document.getElementById('hinh-anh-danh-gia');
    var files = filesInput ? Array.prototype.slice.call(filesInput.files || []) : [];
    var soAnhConLai = (review_panel_state.anh_hien_tai || []).filter(function (anh) {
        return review_panel_state.xoa_anh_ids.indexOf(anh.id) === -1;
    }).length;
    if (soAnhConLai + files.length > 3) {
        thong_bao.innerHTML = '<span style="color:red;">❌ Tổng số ảnh sau cập nhật không được vượt quá 3</span>';
        return;
    }

    var formData = new FormData();
    formData.append('diem', diem);
    formData.append('nhan_xet', nhan_xet);
    formData.append('xoa_anh_ids', (review_panel_state.xoa_anh_ids || []).join(','));
    files.forEach(function (f) { formData.append('hinh_anh', f); });

    fetch('/api/gui-danh-gia/' + cua_hang_id + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': lay_csrf_token() },
        body: formData
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

// ============================================================================
// THONG BAO ADMIN (DON HANG MOI)
// ============================================================================
var admin_notif_timer = null;

function toggle_admin_notif_dropdown() {
    var el = document.getElementById('admin-notif-dropdown');
    if (!el) return;
    el.classList.toggle('open');
    if (el.classList.contains('open')) {
        tai_thong_bao_admin();
    }
}

function khoi_tao_thong_bao_admin() {
    var badge = document.getElementById('admin-notif-badge');
    if (!badge) return;
    tai_thong_bao_admin();
    if (admin_notif_timer) clearInterval(admin_notif_timer);
    admin_notif_timer = setInterval(tai_thong_bao_admin, 15000);
    document.addEventListener('click', function (ev) {
        var wrap = document.querySelector('.admin-notif-wrap');
        var drop = document.getElementById('admin-notif-dropdown');
        if (!wrap || !drop) return;
        if (!wrap.contains(ev.target)) {
            drop.classList.remove('open');
        }
    });
}

function tai_thong_bao_admin() {
    var list = document.getElementById('admin-notif-list');
    var badge = document.getElementById('admin-notif-badge');
    if (!list || !badge) return;
    fetch('/api/admin-thong-bao/')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            var unread = data.unread_count || 0;
            badge.textContent = unread;
            badge.style.display = unread > 0 ? 'inline-block' : 'none';

            var items = data.items || [];
            if (!items.length) {
                list.innerHTML = '<div class="loading" style="padding:10px 12px;">Không có thông báo mới.</div>';
                return;
            }
            var html = '';
            items.forEach(function (it) {
                html += '<a class="admin-notif-item ' + (it.da_doc ? '' : 'unread') + '" href="' + (it.url || '#') + '" style="display:block; text-decoration:none;">';
                html += '<div class="admin-notif-item-title">' + (it.tieu_de || 'Thông báo') + '</div>';
                html += '<div class="admin-notif-item-content">' + (it.noi_dung || '') + '</div>';
                html += '<div class="admin-notif-item-time">' + (it.thoi_gian || '') + '</div>';
                html += '</a>';
            });
            list.innerHTML = html;
        })
        .catch(function () {
            // Bỏ qua lỗi nhẹ để không làm ảnh hưởng map
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


// ============================================================================
// BIEU DO TREN BAN DO - MAP CHARTS (PIE CHART ON MARKERS)
// ============================================================================

var dang_bat_bieu_do = false;
var lop_bieu_do_markers = [];

/**
 * Tao SVG pie chart mini tu phan bo sao
 */
function tao_pie_chart_svg(phan_bo, kich_thuoc) {
    kich_thuoc = kich_thuoc || 40;
    var mau_sac = ['#ff4444', '#ff8800', '#ffcc00', '#8bc34a', '#4caf50'];
    var tong = 0;
    for (var k = 1; k <= 5; k++) tong += (phan_bo[k] || 0);
    if (tong === 0) {
        return '<svg width="' + kich_thuoc + '" height="' + kich_thuoc + '" viewBox="0 0 40 40">' +
            '<circle cx="20" cy="20" r="18" fill="#ddd" stroke="#999" stroke-width="1"/>' +
            '<text x="20" y="24" text-anchor="middle" font-size="11" fill="#999">?</text></svg>';
    }
    var r = 18, cx = 20, cy = 20;
    var goc_hien_tai = -90;
    var duong_dan = '';
    for (var i = 1; i <= 5; i++) {
        var so_luong = phan_bo[i] || 0;
        if (so_luong === 0) continue;
        var goc_cung = (so_luong / tong) * 360;
        if (so_luong === tong) {
            duong_dan += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + mau_sac[i - 1] + '"/>';
        } else {
            var x1 = cx + r * Math.cos(Math.PI * goc_hien_tai / 180);
            var y1 = cy + r * Math.sin(Math.PI * goc_hien_tai / 180);
            var goc_cuoi = goc_hien_tai + goc_cung;
            var x2 = cx + r * Math.cos(Math.PI * goc_cuoi / 180);
            var y2 = cy + r * Math.sin(Math.PI * goc_cuoi / 180);
            var co_lon = goc_cung > 180 ? 1 : 0;
            duong_dan += '<path d="M' + cx + ',' + cy + ' L' + x1.toFixed(2) + ',' + y1.toFixed(2) +
                ' A' + r + ',' + r + ' 0 ' + co_lon + ',1 ' + x2.toFixed(2) + ',' + y2.toFixed(2) +
                ' Z" fill="' + mau_sac[i - 1] + '"/>';
        }
        goc_hien_tai += goc_cung;
    }
    var diem_tb = 0;
    for (var j = 1; j <= 5; j++) diem_tb += j * (phan_bo[j] || 0);
    diem_tb = (diem_tb / tong).toFixed(1);
    return '<svg width="' + kich_thuoc + '" height="' + kich_thuoc + '" viewBox="0 0 40 40">' +
        duong_dan +
        '<circle cx="20" cy="20" r="10" fill="white" stroke="#fff" stroke-width="1"/>' +
        '<text x="20" y="24" text-anchor="middle" font-size="9" font-weight="bold" fill="#333">' + diem_tb + '★</text>' +
        '</svg>';
}

/**
 * Toggle bieu do pie chart tren ban do
 */
function toggle_bieu_do_ban_do() {
    dang_bat_bieu_do = !dang_bat_bieu_do;
    var btn = document.getElementById('btn-toggle-chart');
    if (dang_bat_bieu_do) {
        btn.textContent = '📊 Tắt Biểu Đồ';
        btn.style.background = '#e53e3e';
        hien_bieu_do_tren_ban_do();
    } else {
        btn.textContent = '📊 Biểu Đồ';
        btn.style.background = 'linear-gradient(135deg,#667eea,#764ba2)';
        xoa_bieu_do_tren_ban_do();
    }
}

function hien_bieu_do_tren_ban_do() {
    xoa_bieu_do_tren_ban_do();
    du_lieu_cua_hang.forEach(function (ch) {
        if (!ch.vi_do || !ch.kinh_do || !ch.phan_bo_sao) return;
        var tong = 0;
        for (var k = 1; k <= 5; k++) tong += (ch.phan_bo_sao[k] || 0);
        if (tong === 0) return;
        var svg = tao_pie_chart_svg(ch.phan_bo_sao, 46);
        var icon = L.divIcon({
            html: '<div style="cursor:pointer;" title="' + ch.ten + ' - ' + ch.diem_tb + '★ (' + tong + ' đánh giá)">' + svg + '</div>',
            className: 'marker-bieu-do',
            iconSize: [46, 46],
            iconAnchor: [23, 23]
        });
        var marker = L.marker([ch.vi_do, ch.kinh_do], { icon: icon, interactive: true });
        marker.bindPopup(tao_noi_dung_popup_cua_hang(ch), { minWidth: 200 });
        marker.addTo(ban_do);
        lop_bieu_do_markers.push(marker);
    });
}

function xoa_bieu_do_tren_ban_do() {
    lop_bieu_do_markers.forEach(function (m) { ban_do.removeLayer(m); });
    lop_bieu_do_markers = [];
}


// ============================================================================
// SO SANH CUA HANG - STORE COMPARISON
// ============================================================================

var danh_sach_so_sanh = [];

function toggle_so_sanh(id_cua_hang) {
    var vi_tri = danh_sach_so_sanh.indexOf(id_cua_hang);
    if (vi_tri > -1) {
        danh_sach_so_sanh.splice(vi_tri, 1);
    } else {
        if (danh_sach_so_sanh.length >= 2) {
            danh_sach_so_sanh.shift();
        }
        danh_sach_so_sanh.push(id_cua_hang);
    }
    // Cap nhat UI nutton
    var nut_ss = document.querySelectorAll('.btn-so-sanh');
    nut_ss.forEach(function (btn) {
        var bid = parseInt(btn.getAttribute('data-id'));
        if (danh_sach_so_sanh.indexOf(bid) > -1) {
            btn.style.background = '#e53e3e';
            btn.textContent = '✓ Đã chọn';
        } else {
            btn.style.background = '#667eea';
            btn.textContent = '⚖️ So sánh';
        }
    });
    if (danh_sach_so_sanh.length === 2) {
        hien_modal_so_sanh();
    }
}

function hien_modal_so_sanh() {
    var ch1 = du_lieu_cua_hang.find(function (c) { return c.id === danh_sach_so_sanh[0]; });
    var ch2 = du_lieu_cua_hang.find(function (c) { return c.id === danh_sach_so_sanh[1]; });
    if (!ch1 || !ch2) return;

    var tao_dong = function (nhan, gt1, gt2) {
        return '<tr><td style="font-weight:600; color:#555; padding:10px 12px; background:#f9fafb; width:30%;">' + nhan + '</td>' +
            '<td style="padding:10px 12px; text-align:center;">' + gt1 + '</td>' +
            '<td style="padding:10px 12px; text-align:center;">' + gt2 + '</td></tr>';
    };

    var pie1 = tao_pie_chart_svg(ch1.phan_bo_sao || {}, 60);
    var pie2 = tao_pie_chart_svg(ch2.phan_bo_sao || {}, 60);

    var kc1 = ch1.khoang_cach != null ? ch1.khoang_cach.toFixed(2) + ' km' : 'N/A';
    var kc2 = ch2.khoang_cach != null ? ch2.khoang_cach.toFixed(2) + ' km' : 'N/A';

    var html = '<table style="width:100%; border-collapse:collapse; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">' +
        '<thead><tr><th style="padding:12px; background:#667eea; color:white; width:30%;">Tiêu chí</th>' +
        '<th style="padding:12px; background:#667eea; color:white; width:35%;">' + ch1.ten + '</th>' +
        '<th style="padding:12px; background:#764ba2; color:white; width:35%;">' + ch2.ten + '</th></tr></thead><tbody>' +
        tao_dong('Loại', ch1.loai, ch2.loai) +
        tao_dong('Địa chỉ', ch1.dia_chi, ch2.dia_chi) +
        tao_dong('Điểm TB', '<span style="font-size:1.3em; font-weight:700; color:#f59e0b;">' + (ch1.diem_tb || 0) + ' ★</span>', '<span style="font-size:1.3em; font-weight:700; color:#f59e0b;">' + (ch2.diem_tb || 0) + ' ★</span>') +
        tao_dong('Phân Bố Sao', pie1, pie2) +
        tao_dong('Số Đánh Giá', '<b>' + (ch1.so_danh_gia || 0) + '</b>', '<b>' + (ch2.so_danh_gia || 0) + '</b>') +
        tao_dong('Số Đơn Thanh Toán', '<b>' + (ch1.so_don_thanh_toan || 0) + '</b>', '<b>' + (ch2.so_don_thanh_toan || 0) + '</b>') +
        tao_dong('Khoảng Cách', kc1, kc2) +
        tao_dong('Có Sự Kiện', ch1.co_su_kien ? '<span style="color:green;">✅ Có</span>' : '<span style="color:#999;">❌ Không</span>',
            ch2.co_su_kien ? '<span style="color:green;">✅ Có</span>' : '<span style="color:#999;">❌ Không</span>') +
        '</tbody></table>';

    document.getElementById('noi-dung-so-sanh').innerHTML = html;
    var modal = document.getElementById('modal-so-sanh');
    modal.style.display = 'flex';
}

function dong_modal_so_sanh() {
    document.getElementById('modal-so-sanh').style.display = 'none';
    danh_sach_so_sanh = [];
    // Reset buttons
    var nut_ss = document.querySelectorAll('.btn-so-sanh');
    nut_ss.forEach(function (btn) {
        btn.style.background = '#667eea';
        btn.textContent = '⚖️ So sánh';
    });
}
