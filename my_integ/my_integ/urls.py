from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api import views
from django.contrib.auth import views as auth_views

from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Routes
    path('api/', include('api.urls')),
    path('api/mobile-login/', obtain_auth_token, name='mobile_login'),

    # Frontend Pages
    path('', views.home, name='home'),
    path('shop/', views.home, name='shop'),
    path('profile/', views.profile_view, name='user_profile'), 
    path('store/<int:store_id>/', views.store_profile, name='store_profile'),
    path('cart/', views.view_cart, name='cart'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('history/<int:pk>/', views.purchase_history, name='purchase_history_detail'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/checkout/pay/<int:pk>/', views.checkout_pay, name='checkout_pay'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('store/create/', views.create_store, name='create_store'),
    path('store/<int:store_id>/', views.store_profile, name='store_profile'),
    path('products/create/', views.create_product, name='create_product'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('store/orders/', views.seller_orders, name='store_orders'),
    path('store/<int:store_id>/', views.store_profile, name='store_profile'),
    path('store/manage-products/', views.manage_products, name='manage_products'),
    path('store/edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('store/delete-product/<int:pk>/', views.delete_product, name='delete_product'),


    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
    
    # This line fixes the 'password_reset' error in your profile template
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)