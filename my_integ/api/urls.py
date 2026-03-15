from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf.urls.static import static
from django.conf import settings

router = DefaultRouter()

router.register(r'products',   views.ProductViewSet)
router.register(r'users',      views.UserViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'stores',     views.StoreViewSet)
router.register(r'vouchers',   views.VoucherViewSet)
router.register(r'shipments',  views.ShipmentViewSet)
router.register(r'addresses',  views.AddressViewSet)
router.register(r'payments',   views.PaymentViewSet)
router.register(r'carts',      views.CartViewSet)
router.register(r'orders',     views.OrderViewSet,      basename='order')
router.register(r'reviews',    views.ReviewViewSet,     basename='review')
router.register(r'cartitems',  views.CartItemViewSet,   basename='cartitem')
router.register(r'messages',   views.ChatMessageViewSet, basename='chatmessage')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/pay/<int:pk>/', views.checkout_pay, name='checkout_pay'),
    path('seller/messages/', views.seller_message_center, name='seller_messages'),
    path('profile/', views.profile_view, name='user_profile'),
    path('profile/add-address/', views.add_address, name='add_address'),
    path('store/orders/', views.seller_orders, name='seller_orders'),
    path('inventory/download/', views.download_inventory_pdf, name='download_inventory_pdf'),
    path('product/<int:product_id>/reserve/', views.reserve_product, name='reserve_product'),
    path('reservation/<int:res_id>/complete/', views.complete_reservation, name='complete_reservation'),
    

    
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)