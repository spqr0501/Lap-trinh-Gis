from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ThucHanhApp', '0005_danhgia_nguoi_dung_donhang_nguoi_dung'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module', models.CharField(max_length=100)),
                ('hanh_dong', models.CharField(choices=[('create', 'Tạo mới'), ('update', 'Cập nhật'), ('delete', 'Xóa'), ('view', 'Xem'), ('export', 'Xuất dữ liệu'), ('other', 'Khác')], default='other', max_length=20)),
                ('mo_ta', models.TextField()),
                ('ip_address', models.CharField(blank=True, default='', max_length=50)),
                ('thoi_gian', models.DateTimeField(auto_now_add=True)),
                ('nguoi_dung', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Nhật ký thao tác',
                'verbose_name_plural': 'Nhật ký thao tác',
                'db_table': 'audit_log',
                'ordering': ['-thoi_gian'],
            },
        ),
    ]
