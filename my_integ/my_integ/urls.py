from django.contrib import admin
from django.urls import path, include
from api import views

urlpatterns = [
    path('admin/', admin.site.urls), #
    path('api/', include('api.urls')), #
    
    # NEW: This makes the shop your home page
    path('', views.home, name='home'), 
    
    path('shop/', views.home, name='shop'), #
    path('cart/', views.view_cart, name='cart'), #
]