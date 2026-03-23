from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ThucHanhApp', '0007_danhgialike'),
    ]

    operations = [
        migrations.CreateModel(
            name='DanhGiaAnh',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hinh_anh', models.ImageField(upload_to='danh_gia/')),
                ('thoi_gian_tao', models.DateTimeField(auto_now_add=True)),
                ('danh_gia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hinh_anhs', to='ThucHanhApp.danhgia')),
            ],
            options={
                'verbose_name': 'Ảnh đánh giá',
                'verbose_name_plural': 'Ảnh đánh giá',
                'db_table': 'danh_gia_anh',
                'ordering': ['thoi_gian_tao'],
            },
        ),
        migrations.AddField(
            model_name='auditlog',
            name='doi_tuong',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='doi_tuong_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='du_lieu_sau',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='du_lieu_truoc',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
