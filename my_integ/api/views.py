from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

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

# 2. Order Endpoint with Business, Voucher, and Inventory Logic
@method_decorator(csrf_exempt, name='dispatch')
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 

    def create(self, request, *args, **kwargs):
        # Extract data from the frontend request
        product_id = request.data.get('product_id') # Ensure frontend sends this
        voucher_code = request.data.get('voucher_code')
        total_amount = float(request.data.get('total_amount', 0))
        
        # --- Inventory Check Logic ---
        try:
            product = Product.objects.get(id=product_id)
            # Prevent order if stock is zero or less
            if product.stock_quantity <= 0:
                return Response(
                    {"error": f"Sorry, {product.name} is sold out!"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # --- Voucher Validation Logic ---
        if voucher_code:
            try:
                voucher = Voucher.objects.get(
                    code=voucher_code, 
                    start_date__lte=timezone.now(), 
                    end_date__gte=timezone.now()
                )
                
                if voucher.discount_type == 'Fixed':
                    total_amount -= float(voucher.discount_value)
                else:
                    total_amount -= (total_amount * (float(voucher.discount_value) / 100))
                
                total_amount = max(0, total_amount) # Prevent negative prices
                
            except Voucher.DoesNotExist:
                return Response(
                    {"error": "Invalid or expired voucher code."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # --- Save Order and Update Stock ---
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Perform save and decrement stock in one process
        order = serializer.save(total_amount=total_amount)
        product.stock_quantity -= 1
        product.save() # Persist the new stock count to MySQL
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 3. Product ViewSet with RELATIONAL FILTERING
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'store'] 

# 4. Standard Supporting ViewSets
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