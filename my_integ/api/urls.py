from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 1. Isang Router instance lang ang kailangan
router = DefaultRouter()

# 2. I-register ang lahat ng ViewSets (Siguraduhing isa lang bawat resource)
router.register(r'products', views.ProductViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'stores', views.StoreViewSet)
router.register(r'vouchers', views.VoucherViewSet)
router.register(r'shipments', views.ShipmentViewSet)
router.register(r'addresses', views.AddressViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'carts', views.CartViewSet)

# Importante: Gamitan ng basename kung ang ViewSet ay may custom get_queryset
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'reviews', views.ReviewViewSet, basename='review') 
router.register(r'cartitems', views.CartItemViewSet, basename='cartitem')

# 3. Define ang urlpatterns
urlpatterns = [
    # Ang router-generated URLs (e.g., /api/orders/, /api/products/)
    path('', include(router.urls)),
    
    # Dito mo ilalagay ang path para sa Purchase History template view kung kailangan
    path('history/', views.purchase_history, name='purchase_history'),
]