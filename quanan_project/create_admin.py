"""
Script tạo admin user
Chạy: python create_admin.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quanan_project.settings')

import django
django.setup()

from django.contrib.auth.models import User

# Xóa admin cũ nếu có
User.objects.filter(username='admin').delete()

# Tạo admin mới
User.objects.create_superuser('admin', 'admin@test.com', '123')
print('Admin created: username=admin, password=123')
