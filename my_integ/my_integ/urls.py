from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- API Routes ---
    path('api/', include('api.urls')),

    # --- Frontend Pages ---
    path('', views.home, name='home'),
    path('shop/', views.home, name='shop'),
    path('Cart/cart/', views.view_cart, name='cart'),
    path('history/orders/checkout/', views.purchase_history, name='purchase_history'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('history/<int:pk>/', views.purchase_history, name='purchase_history_detail'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/checkout/pay/<int:pk>/', views.checkout_pay, name='checkout_pay'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # --- Authentication ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)