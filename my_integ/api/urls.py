from django.urls import path, include
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
    # This automatically generates URLs like /api/products/, /api/cartitems/, etc.
    path('', include(router.urls)),
]