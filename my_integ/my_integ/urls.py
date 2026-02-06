from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api import views  # Import views from your 'api' app

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- API Routes (JSON Data) ---
    # This connects to api/urls.py
    path('api/', include('api.urls')),

    # --- Frontend Pages (HTML Views) ---
    path('', views.home, name='home'),
    path('shop/', views.home, name='shop'),
    path('cart/', views.view_cart, name='cart'),
    path('history/', views.purchase_history, name='purchase_history'),
    
    # The Checkout Page (Fixes 404 error)
    path('checkout/', views.checkout_view, name='checkout'), 

    # --- Authentication ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
]

# --- Serve Media Files (Images) in Development ---
# This is CRITICAL for seeing product images
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)