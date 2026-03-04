from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .forms import RegisterForm
from .models import (
    Product, Order, OrderItem, User, Category, Store, 
    Voucher, Shipment, Address, Payment, Cart, CartItem, Review
)
from .serializers import (
    ProductSerializer, OrderSerializer, UserSerializer, 
    CategorySerializer, StoreSerializer, VoucherSerializer, 
    ShipmentSerializer, AddressSerializer, PaymentSerializer,
    CartSerializer, CartItemSerializer, ReviewSerializer
)

# --- 1. AUTHENTICATION VIEWS ---

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            Cart.objects.get_or_create(user=new_user)
            messages.success(request, f'Account created for {new_user.username}! You can now log in.')
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
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart).order_by('product__store__store_name')
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'cart_total': cart_total})

@login_required(login_url='login')
def checkout_view(request):
    product_id = request.GET.get('product_id')
    quantity = int(request.GET.get('quantity', 1))
    address = Address.objects.filter(user=request.user, is_default=True).first()
    
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        items = [{'product': product, 'quantity': quantity, 'item_total': product.price * quantity}]
        merchandise_subtotal = product.price * quantity
    else:
        user_cart, _ = Cart.objects.get_or_create(user=request.user)
        items = CartItem.objects.filter(cart=user_cart)
        merchandise_subtotal = sum(item.quantity * item.product.price for item in items)

    shipping_fee, protection = 115, 4 
    total_payment = merchandise_subtotal + shipping_fee + protection
    
    context = {
        'items': items, 'address': address, 'subtotal': merchandise_subtotal,
        'protection': protection, 'shipping_fee': shipping_fee, 'total_payment': total_payment
    }
    return render(request, 'checkout.html', context)

@login_required(login_url='login')
def purchase_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__product__store', 'shipment', 'payment'
    ).order_by('-order_date')
    return render(request, 'orders/PurchaseHistory.html', {'orders': orders})


# --- 3. API VIEWSETS ---

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer 
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-order_date')

    # CREATE: Place Order Logic (Calculates Prices & Updates Stock)
    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        product_id = data.get('product_id') or data.get('product')
        items_to_process = []
        calculated_total = 0

        # Logic A: Buy Now (Single Item)
        if product_id:
            try:
                prod = Product.objects.get(id=product_id)
                qty = int(data.get('quantity', 1))
                items_to_process.append({'product': prod, 'quantity': qty, 'price': prod.price})
                calculated_total = prod.price * qty
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        # Logic B: Cart Checkout (Multiple Items)
        else:
            cart_items = CartItem.objects.filter(cart__user=user)
            if not cart_items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            for item in cart_items:
                items_to_process.append({'product': item.product, 'quantity': item.quantity, 'price': item.product.price})
                calculated_total += item.product.price * item.quantity

        try:
            with transaction.atomic():
                # Create main Order record
                order = Order.objects.create(
                    user=user,
                    total_amount=calculated_total, 
                    status='to_pay', # Set initial status
                    payment_method=data.get('payment_method', 'COD'),
                    shipping_address=data.get('shipping_address', 'Default Address')
                )
                
                # Create individual OrderItems
                for item in items_to_process:
                    if item['product'].stock_quantity < item['quantity']:
                        raise ValueError(f"Not enough stock for {item['product'].name}")
                    
                    OrderItem.objects.create(
                        order=order, product=item['product'], 
                        quantity=item['quantity'], price=item['price']
                    )
                    
                    # Stock deduction
                    item['product'].stock_quantity -= item['quantity']
                    item['product'].save()

                # Clear Cart if this was a cart order
                if not product_id:
                    CartItem.objects.filter(cart__user=user).delete()

            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # PATCH: Handles Modal buttons (Cancel Order / Confirm Received)
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        
        # Cancel Logic: Return stocks to inventory
        if new_status == 'cancelled' and instance.status != 'cancelled':
            with transaction.atomic():
                for item in instance.items.all():
                    item.product.stock_quantity += item.quantity
                    item.product.save()
                instance.status = 'cancelled'
                instance.save()
            return Response({'status': 'Order cancelled, stock returned.'})

        # Received Logic
        if new_status == 'completed':
            instance.status = 'completed'
            instance.save()
            return Response({'status': 'Order completed successfully.'})

        return super().partial_update(request, *args, **kwargs)

    # ACTION: Submit Review from History Modal
    @action(detail=True, methods=['post'], url_path='submit-review')
    def submit_review(self, request, pk=None):
        order = self.get_object()
        first_item = order.items.first() # Target review to first product
        if not first_item:
            return Response({"error": "No products in order"}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = ReviewSerializer(data={
            'order': order.id,
            'product': first_item.product.id,
            'rating': request.data.get('rating'),
            'comment': request.data.get('text')
        }, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- 4. OTHER API VIEWSETS ---

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
        user_cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=user_cart)
    def perform_create(self, serializer):
        user_cart, _ = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=user_cart)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

class UserViewSet(viewsets.ModelViewSet): queryset = User.objects.all(); serializer_class = UserSerializer
class CategoryViewSet(viewsets.ModelViewSet): queryset = Category.objects.all(); serializer_class = CategorySerializer
class StoreViewSet(viewsets.ModelViewSet): queryset = Store.objects.all(); serializer_class = StoreSerializer
class VoucherViewSet(viewsets.ModelViewSet): queryset = Voucher.objects.all(); serializer_class = VoucherSerializer
class ShipmentViewSet(viewsets.ModelViewSet): queryset = Shipment.objects.all(); serializer_class = ShipmentSerializer
class AddressViewSet(viewsets.ModelViewSet): queryset = Address.objects.all(); serializer_class = AddressSerializer
class PaymentViewSet(viewsets.ModelViewSet): queryset = Payment.objects.all(); serializer_class = PaymentSerializer
class CartViewSet(viewsets.ModelViewSet): queryset = Cart.objects.all(); serializer_class = CartSerializer