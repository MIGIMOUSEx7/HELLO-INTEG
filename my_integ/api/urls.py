from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'stores', views.StoreViewSet)
router.register(r'vouchers', views.VoucherViewSet)
router.register(r'shipments', views.ShipmentViewSet)
router.register(r'addresses', views.AddressViewSet)
router.register(r'payments', views.PaymentViewSet)

# Registered ViewSets for the Cart system
router.register(r'carts', views.CartViewSet)
router.register(r'cartitems', views.CartItemViewSet, basename='cartitem')

urlpatterns = [
    # --- Authentication ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # FIXED: Point 'signup' to 'register_view' since they do the same thing
    path('signup/', views.register_view, name='signup'), 

    # --- Frontend Pages ---
    path('', views.home, name='home'),
    path('shop/', views.home, name='shop'),
    path('cart/', views.view_cart, name='cart'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('checkout/', views.checkout_view, name='checkout'),

    # --- API Root ---
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)