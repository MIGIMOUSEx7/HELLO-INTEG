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
            messages.success(request, f'Account created for {new_user.username}!')
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
            messages.error(request, "Maling username o password.")
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
    
    # Kukuha ng default address para sa Checkout UI
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
    return render(request, 'orders/checkout.html', context)

# api/views.py

@login_required(login_url='login')
def checkout_pay(request, pk):
    # 1. Kunin ang specific order
    order = get_object_or_404(Order, pk=pk, user=request.user)

    # 2. I-prepare ang items mula sa OrderItem model
    # Gagamitin natin ang parehong variable names ('items', 'subtotal') 
    # para hindi na kailangang baguhin ang checkout.html
    items = order.items.all() 
    merchandise_subtotal = order.total_amount - 119 # Reverse calculation (115 shipping + 4 protection)

    context = {
        'order': order,
        'items': items, # Dito nanggagaling ang display sa table
        'address': order.address,
        'subtotal': merchandise_subtotal,
        'shipping_fee': 115,
        'protection': 4,
        'total_payment': order.total_amount
    }

    return render(request, 'orders/checkout.html', context)

@login_required(login_url='login')
def purchase_history(request, pk=None):
    if pk:
        order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk, user=request.user)
        return render(request, 'orders/OrderDetail.html', {'order': order})
    
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-order_date')
    return render(request, 'orders/PurchaseHistory.html', {'orders': orders})

@login_required(login_url='login')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'orders/product_detail.html', {'product': product})


# --- 3. API VIEWSETS ---

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer 
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-order_date')

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        product_id = data.get('product_id') or data.get('product')
        items_to_process = []
        calculated_total = 0

        # KUNIN ANG DEFAULT ADDRESS
        user_address = Address.objects.filter(user=user, is_default=True).first()
        if user_address:
            formatted_address = f"{user_address.street}, {user_address.city}, {user_address.province}, {user_address.zip_code}"
        else:
            formatted_address = data.get('shipping_address', 'Default Address')

        # Buy Now Logic
        if product_id:
            try:
                prod = Product.objects.get(id=product_id)
                qty = int(data.get('quantity', 1))
                items_to_process.append({'product': prod, 'quantity': qty, 'price': prod.price})
                calculated_total = prod.price * qty
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        # Cart Logic
        else:
            cart_items = CartItem.objects.filter(cart__user=user)
            if not cart_items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            for item in cart_items:
                items_to_process.append({'product': item.product, 'quantity': item.quantity, 'price': item.product.price})
                calculated_total += item.product.price * item.quantity

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    total_amount=calculated_total, 
                    status='to_pay',
                    payment_method=data.get('payment_method', 'COD'),
                    address=user_address,
                    shipping_address=formatted_address 
                )
                
                for item in items_to_process:
                    if item['product'].stock_quantity < item['quantity']:
                        raise ValueError(f"Not enough stock for {item['product'].name}")
                    
                    OrderItem.objects.create(
                        order=order, product=item['product'], 
                        quantity=item['quantity'], price=item['price']
                    )
                    
                    item['product'].stock_quantity -= item['quantity']
                    item['product'].save()

                if not product_id:
                    CartItem.objects.filter(cart__user=user).delete()

            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        
        # Pag binalik ang stock pag na-cancel
        if new_status == 'cancelled' and instance.status != 'cancelled':
            with transaction.atomic():
                for item in instance.items.all():
                    item.product.stock_quantity += item.quantity
                    item.product.save()
                instance.status = 'cancelled'
                instance.save()
            return Response({'status': 'Cancelled, stock returned.'})

        if new_status == 'completed':
            instance.status = 'completed'
            instance.save()
            return Response({'status': 'Order received.'})

        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='submit-review')
    def submit_review(self, request, pk=None):
        order = self.get_object()
        first_item = order.items.first()
        if not first_item:
            return Response({"error": "Walang items sa order na ito."}, status=status.HTTP_400_BAD_REQUEST)
            
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

# Utility Viewsets
class UserViewSet(viewsets.ModelViewSet): queryset = User.objects.all(); serializer_class = UserSerializer
class CategoryViewSet(viewsets.ModelViewSet): queryset = Category.objects.all(); serializer_class = CategorySerializer
class StoreViewSet(viewsets.ModelViewSet): queryset = Store.objects.all(); serializer_class = StoreSerializer
class VoucherViewSet(viewsets.ModelViewSet): queryset = Voucher.objects.all(); serializer_class = VoucherSerializer
class ShipmentViewSet(viewsets.ModelViewSet): queryset = Shipment.objects.all(); serializer_class = ShipmentSerializer
class AddressViewSet(viewsets.ModelViewSet): queryset = Address.objects.all(); serializer_class = AddressSerializer
class PaymentViewSet(viewsets.ModelViewSet): queryset = Payment.objects.all(); serializer_class = PaymentSerializer
class CartViewSet(viewsets.ModelViewSet): queryset = Cart.objects.all(); serializer_class = CartSerializer