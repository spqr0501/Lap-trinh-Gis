"""URL routing"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.trang_chu),
    path('api/loai/', views.api_loai),
    path('api/quan/', views.api_quan),
    path('api/timkiem/', views.api_timkiem),
    path('api/goiy/<int:ma_quan>/', views.api_goiy),
]
