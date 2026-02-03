from django import path
from . import views

urlpatterns = [
    path('', views.trang_chu, name='trang_chu'),
]
