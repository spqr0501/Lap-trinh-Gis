from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ThucHanhApp', '0006_auditlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='DanhGiaLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thoi_gian', models.DateTimeField(auto_now_add=True)),
                ('danh_gia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='ThucHanhApp.danhgia')),
                ('nguoi_dung', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='danh_gia_likes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Like đánh giá',
                'verbose_name_plural': 'Like đánh giá',
                'db_table': 'danh_gia_like',
                'ordering': ['-thoi_gian'],
                'unique_together': {('danh_gia', 'nguoi_dung')},
            },
        ),
    ]
