from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path
from api import views

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
router.register(r'cartitems', views.CartItemViewSet)


# The API URLs are now determined automatically by the router
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'), # Your Shop
    path('shop/', views.home, name='shop'), # Your main storefront
    path('cart/', views.view_cart, name='cart'), # NEW: The path to your cart page
    path('history/', views.purchase_history, name='purchase_history'),
    path('', include(router.urls)),         # The API Root at /api/
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
]