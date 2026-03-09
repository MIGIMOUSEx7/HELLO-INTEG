from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.messages import get_messages

from .forms import RegisterForm
from .models import (
    Product, Order, OrderItem, User, Category, Store, 
    Voucher, Shipment, Payment, Address, Cart, CartItem, Review, ChatMessage,
    Profile
)
from .serializers import (
    ProductSerializer, OrderSerializer, UserSerializer, 
    CategorySerializer, StoreSerializer, VoucherSerializer, 
    ShipmentSerializer, AddressSerializer, PaymentSerializer,
    CartSerializer, CartItemSerializer, ReviewSerializer, ChatMessageSerializer
)

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            Cart.objects.get_or_create(user=new_user)
            Profile.objects.get_or_create(user=new_user)
            messages.success(request, f'Account created for {new_user.username}!')
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, 'login/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        user_val = request.POST.get('username')
        pass_val = request.POST.get('password')
        if user_val and pass_val:
            user = authenticate(request, username=user_val, password=pass_val)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Maling username o password.")
        else:
            messages.error(request, "Mangyaring ilagay ang iyong credentials.")
    else:
        list(get_messages(request))
    return render(request, 'login/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "Naka-logout ka na.")
    return redirect('login')

@login_required(login_url='login')
def home(request):
    return render(request, 'shop.html')

def store_profile(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    products = Product.objects.filter(store=store)
    return render(request, 'store_profile.html', {'store': store, 'products': products})

@login_required(login_url='login')
def seller_message_center(request):
    user_stores = Store.objects.filter(user=request.user)
    messages_list = ChatMessage.objects.filter(store__in=user_stores).order_by('-timestamp')
    unique_customers = messages_list.values('sender', 'sender__username', 'store__store_name').distinct()
    return render(request, 'seller/message_center.html', {'customers': unique_customers, 'stores': user_stores})

@login_required(login_url='login')
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        if 'update_info' in request.POST:
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            messages.success(request, "Aking account info ay na-update!")
        
        elif 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            messages.success(request, "Aking litrato ay na-update!")
            
        return redirect('user_profile')

    user_stores = Store.objects.filter(user=request.user)
    user_addresses = Address.objects.filter(user=request.user)
    
    context = {
        'stores': user_stores,
        'addresses': user_addresses,
        'profile': profile,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='login')
def add_address(request):
    if request.method == 'POST':
        addr_data = {
            'user': request.user,
            'full_name': request.POST.get('full_name'),
            'street': request.POST.get('street'),
            'city': request.POST.get('city'),
            'province': request.POST.get('province'),
            'zip_code': request.POST.get('zip_code'),
            'is_default': request.POST.get('is_default') == 'on' or request.POST.get('force_default') == 'true'
        }
        
        fields = [f.name for f in Address._meta.get_fields()]
        if 'phone' in fields:
            addr_data['phone'] = request.POST.get('phone')
        elif 'phone_number' in fields:
            addr_data['phone_number'] = request.POST.get('phone')

        if addr_data['is_default']:
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(**addr_data)
        messages.success(request, "Ang bagong address ay matagumpay na naidagdag!")
        
        previous_url = request.META.get('HTTP_REFERER')
        if previous_url:
            return redirect(previous_url)
            
    return redirect('user_profile')

@login_required(login_url='login')
def view_cart(request):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart).order_by('product__store__store_name')
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'cart_total': cart_total})

@login_required(login_url='login')
def checkout_view(request):
    product_id = request.GET.get('product_id')
    quantity = int(request.GET.get('quantity', 1)) if request.GET.get('quantity') else 1
    
    # --- THE FIX FOR THE INVISIBLE ADDRESS ---
    # First, try to get the default address
    address = Address.objects.filter(user=request.user, is_default=True).first()
    # If there is no default address, just grab ANY address the user has!
    if not address:
        address = Address.objects.filter(user=request.user).first()
    
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
    
    return render(request, 'orders/checkout.html', {
        'items': items, 
        'address': address, 
        'subtotal': merchandise_subtotal,
        'protection': protection, 
        'shipping_fee': shipping_fee, 
        'total_payment': total_payment
    })

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

@login_required(login_url='login')
def checkout_pay(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    items = order.items.all()
    merchandise_subtotal = order.total_amount - 119
    return render(request, 'orders/checkout.html', {
        'order': order, 'items': items, 'address': order.address,
        'subtotal': merchandise_subtotal, 'shipping_fee': 115,
        'protection': 4, 'total_payment': order.total_amount
    })

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        store_id = self.request.query_params.get('store')
        sender_id = self.request.query_params.get('sender')
        queryset = ChatMessage.objects.filter(Q(sender=user) | Q(receiver=user))
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        if sender_id:
            queryset = queryset.filter(Q(sender_id=sender_id) | Q(receiver_id=sender_id))
        return queryset.order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

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
        user_address = Address.objects.filter(user=user, is_default=True).first()
        formatted_address = f"{user_address.street}, {user_address.city}" if user_address else data.get('shipping_address', 'Default Address')
        
        if product_id:
            prod = get_object_or_404(Product, id=product_id)
            qty = int(data.get('quantity', 1))
            items_to_process.append({'product': prod, 'quantity': qty, 'price': prod.price})
            calculated_total = prod.price * qty
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
                    user=user, total_amount=calculated_total + 119, status='Pending',
                    payment_method=data.get('payment_method', 'COD'), address=user_address, shipping_address=formatted_address
                )
                for item in items_to_process:
                    if item['product'].stock_quantity < item['quantity']:
                        raise ValueError(f"Not enough stock for {item['product'].name}")
                    OrderItem.objects.create(order=order, product=item['product'], quantity=item['quantity'], price=item['price'])
                    item['product'].stock_quantity -= item['quantity']
                    item['product'].save()
                if not product_id:
                    CartItem.objects.filter(cart__user=user).delete()
            return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='submit-review')
    def submit_review(self, request, pk=None):
        order = self.get_object()
        first_item = order.items.first()
        if not first_item:
            return Response({"error": "No products in order"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ReviewSerializer(data={
            'order': order.id, 'product': first_item.product.id,
            'rating': request.data.get('rating'), 'comment': request.data.get('text')
        }, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        if new_status == 'Cancelled' and instance.status != 'Cancelled':
            with transaction.atomic():
                for item in instance.items.all():
                    item.product.stock_quantity += item.quantity
                    item.product.save()
                instance.status = 'Cancelled'
                instance.save()
            return Response({'status': 'Cancelled, stock returned.'})
        return super().partial_update(request, *args, **kwargs)

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

class UserViewSet(viewsets.ModelViewSet): queryset = User.objects.all(); serializer_class = UserSerializer
class CategoryViewSet(viewsets.ModelViewSet): queryset = Category.objects.all(); serializer_class = CategorySerializer
class StoreViewSet(viewsets.ModelViewSet): queryset = Store.objects.all(); serializer_class = StoreSerializer
class VoucherViewSet(viewsets.ModelViewSet): queryset = Voucher.objects.all(); serializer_class = VoucherSerializer
class ShipmentViewSet(viewsets.ModelViewSet): queryset = Shipment.objects.all(); serializer_class = ShipmentSerializer
class AddressViewSet(viewsets.ModelViewSet): queryset = Address.objects.all(); serializer_class = AddressSerializer
class PaymentViewSet(viewsets.ModelViewSet): queryset = Payment.objects.all(); serializer_class = PaymentSerializer
class CartViewSet(viewsets.ModelViewSet): queryset = Cart.objects.all(); serializer_class = CartSerializer
class ReviewViewSet(viewsets.ModelViewSet): queryset = Review.objects.all(); serializer_class = ReviewSerializer