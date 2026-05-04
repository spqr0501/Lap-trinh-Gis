import os
import sys
import django

# Add the project directory to sys.path
sys.path.append(r'e:\LaptrinhGis\ThucHanh')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ThucHanh.settings')
django.setup()

from ThucHanhApp.models import DanhMuc, MatHang

# Get or create categories
cat_map = {
    'nuoc_uong': DanhMuc.objects.get(ten_danh_muc='Nước uống'),
    'thuc_pham': DanhMuc.objects.get(ten_danh_muc='Thực phẩm'),
    'banh_keo': DanhMuc.objects.get(ten_danh_muc='Bánh kẹo'),
    'sua': DanhMuc.objects.get(ten_danh_muc='Sữa & Sản phẩm từ sữa'),
}

# Auto-assign for existing dummy data
items = MatHang.objects.all()
for item in items:
    name_lower = item.ten_mat_hang.lower()
    if 'aquafina' in name_lower or 'coca cola' in name_lower or 'nước' in name_lower:
        item.danh_muc = cat_map['nuoc_uong']
    elif 'mì tôm' in name_lower or 'sandwich' in name_lower or 'phở' in name_lower or 'thịt' in name_lower:
        item.danh_muc = cat_map['thuc_pham']
    elif 'bánh' in name_lower or 'kẹo' in name_lower or 'snack' in name_lower:
        item.danh_muc = cat_map['banh_keo']
    elif 'sữa' in name_lower or 'vinamilk' in name_lower or 'th true milk' in name_lower:
        item.danh_muc = cat_map['sua']
    item.save()

print(f'Assigned categories to {items.count()} items!')
