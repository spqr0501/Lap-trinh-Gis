from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ThucHanhApp', '0008_danhgiaanh_auditlog_diff_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminThongBao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tieu_de', models.CharField(max_length=255)),
                ('noi_dung', models.TextField(blank=True, default='')),
                ('da_doc', models.BooleanField(default=False)),
                ('thoi_gian_tao', models.DateTimeField(auto_now_add=True)),
                ('thoi_gian_doc', models.DateTimeField(blank=True, null=True)),
                ('don_hang', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admin_thong_baos', to='ThucHanhApp.donhang')),
                ('nguoi_dung', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admin_thong_baos', to='auth.user')),
            ],
            options={
                'verbose_name': 'Thông báo admin',
                'verbose_name_plural': 'Thông báo admin',
                'db_table': 'admin_thong_bao',
                'ordering': ['-thoi_gian_tao'],
            },
        ),
    ]
