from django.shortcuts import render
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import (
    Product, Order, User, Category, Store, 
    Voucher, Shipment, Address, Payment
)
from .serializers import (
    ProductSerializer, OrderSerializer, UserSerializer, 
    CategorySerializer, StoreSerializer, VoucherSerializer, 
    ShipmentSerializer, AddressSerializer, PaymentSerializer
)

# 1. Main Storefront View
def home(request):
    """
    Serves the shop.html frontend.
    """
    return render(request, 'shop.html')

# 2. Order Endpoint (With CSRF Bypass)
# This fixes the "POST /api/orders/ 403 Forbidden" error
@method_decorator(csrf_exempt, name='dispatch')
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 

# 3. Supporting ViewSets for ERD Tables
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer

class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer