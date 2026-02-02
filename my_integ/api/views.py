from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Product, Order, User, Category, Store, 
    Voucher, Shipment, Address, Payment,
    Cart, CartItem 
)
from .serializers import (
    ProductSerializer, OrderSerializer, UserSerializer, 
    CategorySerializer, StoreSerializer, VoucherSerializer, 
    ShipmentSerializer, AddressSerializer, PaymentSerializer,
    CartSerializer, CartItemSerializer 
)

def home(request):
    """Serves the main storefront with the integrated floating cart."""
    return render(request, 'shop.html')

# 1. Frontend Template Views
def home(request):
    """Serves the main shop.html frontend storefront."""
    return render(request, 'shop.html')

def view_cart(request):
    """Serves the cart.html page."""
    return render(request, 'cart.html')

# 2. Order Endpoint with Business, Voucher, and Inventory Logic
@method_decorator(csrf_exempt, name='dispatch')
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 

    

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        voucher_code = request.data.get('voucher_code')
        # Use the aggregate total sent from the frontend
        total_amount = float(request.data.get('total_amount', 0))
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock_quantity <= 0:
                return Response(
                    {"error": f"Sorry, {product.name} is sold out!"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Voucher Logic: Fixed vs Percentage
        if voucher_code:
            try:
                voucher = Voucher.objects.get(
                    code=voucher_code, 
                    start_date__lte=timezone.now(), 
                    end_date__gte=timezone.now()
                )
                
                discount_val = float(voucher.discount_value)
                
                if voucher.discount_type == 'Fixed':
                    # Flat subtraction
                    total_amount -= discount_val
                else:
                    # Percentage math: total * (1 - discount/100)
                    total_amount = total_amount * (1 - (discount_val / 100))
                
                # Guardrail: Ensure price never drops below 0 and round for MySQL
                total_amount = max(0, round(total_amount, 2))
                
            except Voucher.DoesNotExist:
                return Response(
                    {"error": "Invalid or expired voucher code."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save order with combined total and update stock count
        order = serializer.save(total_amount=total_amount)
        product.stock_quantity -= 1
        product.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 3. Cart ViewSets
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

@method_decorator(csrf_exempt, name='dispatch')
class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

# 4. Product ViewSet with RELATIONAL FILTERING
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'store'] 

# 5. Standard Supporting ViewSets
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