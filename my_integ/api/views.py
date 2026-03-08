from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction # Needed for atomic database updates
from django.db.models import F, Sum

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .forms import RegisterForm
from .models import (
    Product, Order, OrderItem, User, Category, Store, 
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

# 👇 ADDED: STORE PROFILE VIEW 👇
def store_profile(request, store_id):
    # Fetch the specific store, or return a 404 error if it doesn't exist
    store = get_object_or_404(Store, id=store_id)
    
    # Fetch ONLY the products linked to this store
    products = Product.objects.filter(store=store)
    
    context = {
        'store': store,
        'products': products
    }
    return render(request, 'store_profile.html', context)

@login_required(login_url='login')
def view_cart(request):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart).order_by('product__store__store_name')
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
        # Cart Checkout Flow
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
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    context = {'orders': orders}
    return render(request, 'orders/PurchaseHistory.html', context)


# --- 3. API VIEWSETS ---

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-order_date')
    serializer_class = OrderSerializer 
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        
        # 1. Gather Items & Calculate Total
        product_id = data.get('product') or data.get('product_id')
        items_to_process = []
        calculated_total = 0

        if product_id:
            # Case A: Buy Now (Single Item)
            try:
                prod = Product.objects.get(id=product_id)
                qty = int(data.get('quantity', 1))
                items_to_process.append({'product': prod, 'quantity': qty})
                calculated_total += prod.price * qty
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Case B: Cart Checkout (Multiple Items)
            user_cart, _ = Cart.objects.get_or_create(user=user)
            cart_items = CartItem.objects.filter(cart=user_cart)
            
            if not cart_items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            
            for item in cart_items:
                items_to_process.append({'product': item.product, 'quantity': item.quantity})
                calculated_total += item.product.price * item.quantity

        # 2. Atomic Transaction: Create Order -> Create Items -> Update Stock
        try:
            with transaction.atomic():
                # A. Create the Parent Order
                # We do NOT pass 'product' or 'quantity' here anymore.
                order = Order.objects.create(
                    user=user,
                    total_amount=calculated_total, 
                    status='Pending',
                    payment_method=data.get('payment_method', 'COD'),
                    shipping_address=data.get('shipping_address', 'Default Address')
                )
                
                # B. Create the Children (OrderItems)
                for item in items_to_process:
                    product = item['product']
                    quantity = item['quantity']
                    
                    if product.stock_quantity < quantity:
                        raise ValueError(f"Not enough stock for {product.name}")

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                    
                    # Deduct Stock
                    product.stock_quantity -= quantity
                    product.save()

                # C. Clear Cart only if it was a cart checkout
                if not product_id:
                    CartItem.objects.filter(cart__user=user).delete()

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Order Error: {e}") 
            return Response({"error": "An error occurred processing the order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'store'] 

@method_decorator(csrf_exempt, name='dispatch')
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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