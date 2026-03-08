from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Register each ViewSet ONCE only
router.register(r'products',   views.ProductViewSet)
router.register(r'users',      views.UserViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'stores',     views.StoreViewSet)
router.register(r'vouchers',   views.VoucherViewSet)
router.register(r'shipments',  views.ShipmentViewSet)
router.register(r'addresses',  views.AddressViewSet)
router.register(r'payments',   views.PaymentViewSet)
router.register(r'carts',      views.CartViewSet)
router.register(r'orders',     views.OrderViewSet,     basename='order')
router.register(r'reviews',    views.ReviewViewSet,    basename='review')
router.register(r'cartitems',  views.CartItemViewSet,  basename='cartitem')


urlpatterns = [
    path('', include(router.urls)),
    path('checkout/pay/<int:pk>/', views.checkout_view, name='checkout_pay'),
]