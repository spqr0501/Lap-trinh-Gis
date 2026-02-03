from django.shortcuts import render

# Create your views here.

def trang_chu(request):

    return render(request, 'ThucHanhApp/bando.html')
