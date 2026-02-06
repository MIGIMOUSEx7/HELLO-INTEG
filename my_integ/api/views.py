from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum

from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .forms import RegisterForm
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

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            # SAFE CART CREATION: Uses get_or_create to avoid duplicates/errors
            Cart.objects.get_or_create(user=new_user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, 'login/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        user_val = request.POST.get('username')
        pass_val = request.POST.get('password')
        user = authenticate(request, username=user_val, password=pass_val)
        if user is not None:
            login(request, user)
            return redirect('home') 
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


# --- 2. FRONTEND TEMPLATE VIEWS ---

@login_required(login_url='login')
def home(request):
    return render(request, 'shop.html')

@login_required(login_url='login')
def view_cart(request):
    """
    Fetches cart items for the logged-in user.
    CRITICAL FIX: 2-step lookup to prevent 'ValueError' crashes.
    """
    # 1. Get the actual Cart object first
    user_cart, _ = Cart.objects.get_or_create(user=request.user)

    # 2. Filter items using the Cart object
    cart_items = CartItem.objects.filter(cart=user_cart).order_by('product__store__store_name')
    
    # Calculate total safely
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total
    }
    return render(request, 'cart.html', context)

@login_required(login_url='login')
def checkout_view(request):
    product_id = request.GET.get('product_id')
    quantity = int(request.GET.get('quantity', 1))
    
    if product_id:
        # Buy Now Flow
        product = get_object_or_404(Product, id=product_id)
        items = [{
            'product': product,
            'quantity': quantity,
            'item_total': product.price * quantity
        }]
        merchandise_subtotal = product.price * quantity
    else:
        # Cart Checkout Flow - Safe Lookup
        user_cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=user_cart)
        items = cart_items
        merchandise_subtotal = sum(item.quantity * item.product.price for item in cart_items)

    shipping_fee = 115 
    merchandise_protection = 4 
    total_payment = merchandise_subtotal + shipping_fee + merchandise_protection
    
    address = Address.objects.filter(user=request.user, is_default=True).first()

    context = {
        'items': items,
        'address': address,
        'subtotal': merchandise_subtotal,
        'protection': merchandise_protection,
        'shipping_fee': shipping_fee,
        'total_payment': total_payment
    }
    return render(request, 'checkout.html', context)

@login_required(login_url='login')
def purchase_history(request):
    # FIX: Use 'user_id' to strictly match database column
    orders = Order.objects.filter(user_id=request.user.id).order_by('-order_date')
    context = {'orders': orders}
    return render(request, 'orders/PurchaseHistory.html', context)


# --- 3. API VIEWSETS ---

@method_decorator(csrf_exempt, name='dispatch')
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product') or request.data.get('product_id')
        voucher_code = request.data.get('voucher_code')
        total_amount = float(request.data.get('total_amount', 0))
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock_quantity <= 0:
                return Response(
                    {"error": f"Sorry, {product.product_name} is sold out!"}, 
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

        mutable_data = request.data.copy()
        mutable_data['product'] = product_id
        mutable_data['user'] = request.user.id 

        serializer = self.get_serializer(data=mutable_data)
        if not serializer.is_valid():
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
    serializer_class = CartItemSerializer

    def get_queryset(self):
        # Safe lookup for API as well
        if not self.request.user.is_authenticated:
            return CartItem.objects.none()
        user_cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=user_cart)

    def perform_create(self, serializer):
        user_cart, _ = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=user_cart)

class UserViewSet(viewsets.ModelViewSet): queryset = User.objects.all(); serializer_class = UserSerializer
class CategoryViewSet(viewsets.ModelViewSet): queryset = Category.objects.all(); serializer_class = CategorySerializer
class StoreViewSet(viewsets.ModelViewSet): queryset = Store.objects.all(); serializer_class = StoreSerializer
class VoucherViewSet(viewsets.ModelViewSet): queryset = Voucher.objects.all(); serializer_class = VoucherSerializer
class ShipmentViewSet(viewsets.ModelViewSet): queryset = Shipment.objects.all(); serializer_class = ShipmentSerializer
class AddressViewSet(viewsets.ModelViewSet): queryset = Address.objects.all(); serializer_class = AddressSerializer
class PaymentViewSet(viewsets.ModelViewSet): queryset = Payment.objects.all(); serializer_class = PaymentSerializer
class CartViewSet(viewsets.ModelViewSet): queryset = Cart.objects.all(); serializer_class = CartSerializer