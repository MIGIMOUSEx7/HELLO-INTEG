from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api import views

from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Routes
    path('api/', include('api.urls')),
    path('api/mobile-login/', obtain_auth_token, name='mobile_login'),

    # Frontend Pages
    path('', views.home, name='home'),
    path('shop/', views.home, name='shop'),
    path('store/<int:store_id>/', views.store_profile, name='store_profile'),
    path('cart/', views.view_cart, name='cart'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('history/<int:pk>/', views.purchase_history, name='purchase_history_detail'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/checkout/pay/<int:pk>/', views.checkout_pay, name='checkout_pay'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)