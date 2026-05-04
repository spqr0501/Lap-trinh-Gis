import os
import sys
import django

# Add the project directory to sys.path
sys.path.append(r'e:\LaptrinhGis\ThucHanh')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ThucHanh.settings')
django.setup()

from ThucHanhApp.models import DanhMuc

cats = [
    'Nước uống',
    'Thực phẩm',
    'Đồ dùng',
    'Bánh kẹo',
    'Gia vị',
    'Đồ hộp',
    'Sữa & Sản phẩm từ sữa',
    'Chăm sóc cá nhân',
    'Đồ gia dụng',
    'Văn phòng phẩm',
]

for c in cats:
    DanhMuc.objects.get_or_create(ten_danh_muc=c)

print(f'Done! Total: {DanhMuc.objects.count()} danh muc')
