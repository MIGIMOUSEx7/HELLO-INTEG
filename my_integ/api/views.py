from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
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

# --- 1. AUTHENTICATION VIEWS ---

def signup_view(request):
    """Handles new user registration for your shop."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save() # Saves to MySQL auth_user table
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'login/signup.html', {'form': form})

def login_view(request):
    """Handles user login and session creation."""
    if request.method == 'POST':
        user_val = request.POST.get('username')
        pass_val = request.POST.get('password')
        
        user = authenticate(request, username=user_val, password=pass_val)
        if user is not None:
            login(request, user)
            return redirect('home') 
        else:
            messages.error(request, "Invalid username or password")
            
    return render(request, 'login.html')

def logout_view(request):
    """Logs the user out and redirects to login page."""
    logout(request)
    return redirect('login')


# --- 2. FRONTEND TEMPLATE VIEWS ---

@login_required(login_url='login')
def home(request):
    """Serves the main shop storefront (Protected by Login)."""
    return render(request, 'shop.html')

def view_cart(request):
    """Serves the aggregate cart page."""
    return render(request, 'cart.html')

@login_required(login_url='login')
def purchase_history(request):
    """Serves the history page using the 'orders/' subfolder path."""
    return render(request, 'orders/PurchaseHistory.html')


# --- 3. API VIEWSETS ---

@method_decorator(csrf_exempt, name='dispatch')
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 

    def create(self, request, *args, **kwargs):
        # Support both 'product' and 'product_id' keys to prevent 400 errors
        product_id = request.data.get('product') or request.data.get('product_id')
        voucher_code = request.data.get('voucher_code')
        
        total_amount_raw = request.data.get('total_amount', 0)
        total_amount = float(total_amount_raw) if total_amount_raw else 0.0
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock_quantity <= 0:
                return Response(
                    {"error": f"Sorry, {product.name} is sold out!"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (Product.DoesNotExist, ValueError):
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if voucher_code:
            try:
                voucher = Voucher.objects.get(
                    code=voucher_code, 
                    start_date__lte=timezone.now(), 
                    end_date__gte=timezone.now()
                )
                discount_val = float(voucher.discount_value)
                if voucher.discount_type == 'Fixed':
                    total_amount -= discount_val
                else:
                    total_amount = total_amount * (1 - (discount_val / 100))
                
                total_amount = max(0, round(total_amount, 2))
            except Voucher.DoesNotExist:
                return Response({"error": "Invalid voucher."}, status=status.HTTP_400_BAD_REQUEST)

        # Sync data for Serializer validation
        mutable_data = request.data.copy()
        mutable_data['product'] = product_id

        serializer = self.get_serializer(data=mutable_data)
        if not serializer.is_valid():
            print("Serializer Errors:", serializer.errors) # Debugging on Mac terminal
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        order = serializer.save(total_amount=total_amount)
        product.stock_quantity -= 1
        product.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'store'] 

@method_decorator(csrf_exempt, name='dispatch')
class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

# Standard ViewSets
class UserViewSet(viewsets.ModelViewSet): queryset = User.objects.all(); serializer_class = UserSerializer
class CategoryViewSet(viewsets.ModelViewSet): queryset = Category.objects.all(); serializer_class = CategorySerializer
class StoreViewSet(viewsets.ModelViewSet): queryset = Store.objects.all(); serializer_class = StoreSerializer
class VoucherViewSet(viewsets.ModelViewSet): queryset = Voucher.objects.all(); serializer_class = VoucherSerializer
class ShipmentViewSet(viewsets.ModelViewSet): queryset = Shipment.objects.all(); serializer_class = ShipmentSerializer
class AddressViewSet(viewsets.ModelViewSet): queryset = Address.objects.all(); serializer_class = AddressSerializer
class PaymentViewSet(viewsets.ModelViewSet): queryset = Payment.objects.all(); serializer_class = PaymentSerializer
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer



def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # This saves the user to your MariaDB/MySQL database
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')  # Redirect to login page after success
    else:
        form = UserCreationForm()
    
    return render(request, 'login/signup.html', {'form': form})