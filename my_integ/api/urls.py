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
router.register(r'vouchers', views.VoucherViewSet)   # Matches image_02ec24.png
router.register(r'shipments', views.ShipmentViewSet) # Matches image_02ec24.png
router.register(r'addresses', views.AddressViewSet)  # Matches image_02ec24.png
router.register(r'payments', views.PaymentViewSet)    # Matches image_02ec24.png

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('shop/', views.home, name='shop'), # Your frontend storefront
    path('', include(router.urls)),         # The API Root at /api/
]