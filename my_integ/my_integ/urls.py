from django.contrib import admin
from django.urls import path, include # <--- Make sure both are here
from api.views import home 

urlpatterns = [
    path('', home), 
    path('admin/', admin.site.urls), # Fixed from previous typo
    path('api/', include('api.urls')), 
]