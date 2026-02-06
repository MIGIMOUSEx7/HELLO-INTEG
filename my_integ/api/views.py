from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction # <--- CRITICAL: Needed for bulk order creation
from django.db.models import F, Sum

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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

class OrderViewSet(viewsets.ModelViewSet):
    """
    Handles creating orders. 
    Now supports both Single Item (Buy Now) and Bulk Cart Checkout.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 
    permission_classes = [IsAuthenticated] # Ensure only logged-in users can order

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        
        # 1. Determine items to order
        # If 'product_id' is provided in JSON, it's a "Buy Now" single item order.
        # Otherwise, we fetch everything from the user's Cart.
        product_id = data.get('product') or data.get('product_id')
        items_to_process = []

        if product_id:
            # --- Single Item (Buy Now) ---
            try:
                prod = Product.objects.get(id=product_id)
                qty = int(data.get('quantity', 1))
                items_to_process.append({'product': prod, 'quantity': qty})
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # --- Cart Checkout ---
            user_cart, _ = Cart.objects.get_or_create(user=user)
            cart_items = CartItem.objects.filter(cart=user_cart)
            
            if not cart_items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            
            for item in cart_items:
                items_to_process.append({'product': item.product, 'quantity': item.quantity})

        # 2. Process the Order(s) safely using a transaction
        # This ensures all orders are created at once, or none at all if an error occurs.
        created_orders = []
        try:
            with transaction.atomic():
                for item in items_to_process:
                    product = item['product']
                    quantity = item['quantity']
                    
                    # Stock Check
                    if product.stock_quantity < quantity:
                        raise ValueError(f"Not enough stock for {product.product_name}")

                    # Calculate Price
                    total_amount = product.price * quantity
                    
                    # Create the Order Record
                    order = Order.objects.create(
                        user=user,
                        product=product,
                        quantity=quantity,
                        total_amount=total_amount,
                        status='Pending', # Default status
                        payment_method=data.get('payment_method', 'COD'),
                        shipping_address=data.get('shipping_address', 'Default Address')
                    )
                    
                    # Update Stock
                    product.stock_quantity -= quantity
                    product.save()
                    
                    created_orders.append(order)

                # 3. If this was a Cart checkout, clear the cart now that orders are placed
                if not product_id:
                    CartItem.objects.filter(cart__user=user).delete()

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the actual error for debugging
            print(f"Order Processing Error: {e}")
            return Response({"error": "An error occurred processing the order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return success. If multiple orders, we just return the data of the first one to satisfy the serializer.
        if created_orders:
            serializer = self.get_serializer(created_orders[0])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
             return Response({"error": "No orders created"}, status=status.HTTP_400_BAD_REQUEST)


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
        # Safe lookup for API: ensures user is logged in
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