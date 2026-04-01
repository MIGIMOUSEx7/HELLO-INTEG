from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template.loader import get_template
from decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from .models import Voucher
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view
# views.py
from django_filters.rest_framework import DjangoFilterBackend
from .models import OrderItem
from .serializers import OrderItemSerializer
from rest_framework import viewsets
from .serializers import ProductSerializer




# PDF Generation Imports
from xhtml2pdf import pisa
import io
from decimal import Decimal
import datetime

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.messages import get_messages
from rest_framework import viewsets
from .models import Reservation
from .serializers import ReservationSerializer
from .models import Product, Store, Category
from rest_framework import viewsets


from .forms import RegisterForm
from .models import (
    Product, Order, OrderItem, User, Category, Store, 
    Voucher, Shipment, Payment, Address, Cart, CartItem, Review, ChatMessage,
    Profile, Reservation
)
from .serializers import (
    ProductSerializer, OrderSerializer, UserSerializer, 
    CategorySerializer, StoreSerializer, VoucherSerializer, 
    ShipmentSerializer, AddressSerializer, PaymentSerializer,
    CartSerializer, CartItemSerializer, ReviewSerializer, ChatMessageSerializer, ReservationSerializer, ProfileSerializer
)

# ─────────────────────────────────────────
#   AUTHENTICATION & ROUTING
# ─────────────────────────────────────────

@login_required(login_url='login')
def download_inventory_pdf(request):
    """Generates an Official Report with both Inventory and Sales data."""
    user_store = Store.objects.filter(user=request.user).first()
    if not user_store:
        return HttpResponse("Wala kang tindahan!", status=404)

    products = Product.objects.filter(store=user_store)
    
    # 1. Inventory Asset Value (Current Stock)
    total_asset_value = sum((p.price * p.stock_quantity for p in products), Decimal('0.00'))
    
    # 2. Calculate Total Sales (Deliveries + Pickups)
    store_orders = OrderItem.objects.filter(product__store=user_store, order__status='Completed')
    order_earnings = sum((item.price * item.quantity for item in store_orders), Decimal('0.00'))
    order_items_sold = sum((item.quantity for item in store_orders), 0)
    
    completed_res = Reservation.objects.filter(product__store=user_store, status='Completed')
    res_earnings = sum((res.product.price * res.quantity for res in completed_res), Decimal('0.00'))
    res_items_sold = sum((res.quantity for res in completed_res), 0)

    # 3. Combine for Grand Totals
    total_earnings = order_earnings + res_earnings
    total_items_sold = order_items_sold + res_items_sold
    
    context = {
        'products': products,
        'store': user_store,
        'total_count': products.count(),
        'out_of_stock': products.filter(stock_quantity=0).count(),
        'total_value': total_asset_value,
        'total_earnings': total_earnings,        # <-- NEW
        'total_items_sold': total_items_sold,    # <-- NEW
    }
    
    template = get_template('seller/inventory_pdf.html')
    html = template.render(context)
    
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="AgriResQ_Report_{user_store.store_name}.pdf"'
        return response
        
    return HttpResponse("Nagkaroon ng error sa pag-generate ng PDF.", status=400)

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
                if user.is_superuser:
                    return redirect('admin_terminal')
                profile, _ = Profile.objects.get_or_create(user=user)
                if profile.is_seller:
                    return redirect('manage_products')
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

# ─────────────────────────────────────────
#   USER INTERFACE & DASHBOARD
# ─────────────────────────────────────────

@login_required(login_url='login')
def home(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # --- TRAFFIC COP REDIRECTS ---
    # If the user is a seller, redirect them directly to the Seller Dashboard
    if profile.is_seller:
        return redirect('manage_products')
    
    # If the user is an admin, redirect them to the Admin Terminal
    if request.user.is_superuser:
        return redirect('admin_terminal')
    # -----------------------------
        
    return render(request, 'shop.html', {
        'is_seller': profile.is_seller,
        'is_admin': request.user.is_superuser
    })

def store_profile(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    products = Product.objects.filter(store=store)
    is_seller = False
    is_admin = False
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        is_seller = profile.is_seller
        is_admin = request.user.is_superuser
    return render(request, 'store_profile.html', {
        'store': store, 'products': products, 'is_seller': is_seller, 'is_admin': is_admin
    })

@login_required(login_url='login')
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    user_store = Store.objects.filter(user=request.user).first()
    user_address = Address.objects.filter(user=request.user, is_default=True).first()
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'profile':
            full_name = request.POST.get('full_name', '')
            names = full_name.split(' ', 1)
            request.user.first_name = names[0] if len(names) > 0 else ''
            request.user.last_name = names[1] if len(names) > 1 else ''
            request.user.email = request.POST.get('email', '')
            request.user.save()
            profile.phone_number = request.POST.get('phone', '')
            profile.save()
            address = Address.objects.filter(user=request.user, is_default=True).first() or Address(user=request.user, is_default=True)
            address.full_name = full_name
            address.phone = request.POST.get('phone', '')
            address.street = request.POST.get('street', '')
            address.city = request.POST.get('city', '')
            address.province = request.POST.get('province', '')
            address.zip_code = request.POST.get('zip_code', '')
            address.country = "Philippines"
            address.save()
            messages.success(request, "Ang iyong impormasyon ay na-save na!")
        elif form_type == 'picture':
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
                profile.save()
                messages.success(request, "Ang profile picture ay na-update!")
        elif form_type == 'password':
            old_p = request.POST.get('old_password')
            n1 = request.POST.get('new_password1')
            n2 = request.POST.get('new_password2')
            if request.user.check_password(old_p):
                if n1 == n2:
                    request.user.set_password(n1)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, "Password matagumpay na napalitan!")
                else: messages.error(request, "Hindi magkapareho ang bagong password.")
            else: messages.error(request, "Mali ang kasalukuyang password.")
        return redirect('user_profile')

    profile.full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    return render(request, 'profile.html', {
        'profile': profile, 'address': user_address, 'is_approved_seller': profile.is_seller,
        'has_store': user_store is not None, 'store': user_store
    })

# ─────────────────────────────────────────
#   SELLER & ADMIN MANAGEMENT
# ─────────────────────────────────────────

@login_required
def admin_terminal(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied.")
        return redirect('home')

    # --- BASIC COUNTS ---
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_stores = Store.objects.count()
    total_orders = Order.objects.count()

    # --- ORDER STATUS ---
    completed_orders = Order.objects.filter(status='Completed')
    pending_orders = Order.objects.filter(status='Pending').count()

    # --- SALES ---
    total_sales = completed_orders.aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0

    # --- RESERVATIONS ---
    total_reservations = Reservation.objects.count()
    active_reservations = Reservation.objects.filter(status='Active').count()
    completed_reservations = Reservation.objects.filter(status='Completed')

    reservation_earnings = sum(
        (r.product.price * r.quantity for r in completed_reservations),
        Decimal('0.00')
    )

    # --- COMBINED REVENUE ---
    total_revenue = total_sales + reservation_earnings

    # --- INVENTORY STATUS ---
    low_stock = Product.objects.filter(stock_quantity__lte=5).count()
    out_of_stock = Product.objects.filter(stock_quantity=0).count()

    # --- TOP PRODUCTS ---
    top_products = (
        OrderItem.objects.values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    # --- CATEGORY TRENDS ---
    category_trends = Category.objects.annotate(
        p_count=models.Count('product')
    ).order_by('-p_count')

    # --- RECENT USERS ---
    system_users = User.objects.all().order_by('-date_joined')[:10]

    # --- CHAT ACTIVITY ---
    total_messages = ChatMessage.objects.count()

    # --- SALES GRAPH ---
    six_months_ago = timezone.now() - datetime.timedelta(days=180)

    monthly_sales = (
        Order.objects.filter(
            status='Completed',
            order_date__gte=six_months_ago
        )
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    sales_labels = [d['month'].strftime("%b %Y") for d in monthly_sales]
    sales_values = [float(d['total']) for d in monthly_sales]

    return render(request, 'admin/admin_terminal.html', {
        'total_users': total_users,
        'total_products': total_products,
        'total_stores': total_stores,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'total_messages': total_messages,
        'category_trends': category_trends,
        'system_users': system_users,
        'top_products': top_products,
        'sales_labels': sales_labels,
        'sales_values': sales_values,
    })



@login_required(login_url='login')
def manage_products(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user_store = Store.objects.filter(user=request.user).first()
    
    if profile.is_seller and not user_store:
        return redirect('create_store')
    if not profile.is_seller:
        return redirect('user_profile')
    
    products = Product.objects.filter(store=user_store).order_by('-created_at')
    
    # 1. Calculate Standard Online Orders
    store_orders = OrderItem.objects.filter(product__store=user_store, order__status='Completed')
    order_earnings = sum((item.price * item.quantity for item in store_orders), Decimal('0.00'))
    order_items_sold = sum((item.quantity for item in store_orders), 0)
    
    # 2. Calculate Completed In-Person Reservations
    completed_res = Reservation.objects.filter(product__store=user_store, status='Completed')
    res_earnings = sum((res.product.price * res.quantity for res in completed_res), Decimal('0.00'))
    res_items_sold = sum((res.quantity for res in completed_res), 0)

    # 3. Combine for Grand Totals
    total_earnings = order_earnings + res_earnings
    total_items_sold = order_items_sold + res_items_sold
    
    # --- FIX: Fetch the missing variables for the template ---
    active_claims = Reservation.objects.filter(product__store=user_store, status='Active')
    
    # This is the specific variable the template is crying about:
    pending_standard_orders = OrderItem.objects.filter(
        product__store=user_store, 
        order__status='Pending'
    ).select_related('order', 'order__user')

    return render(request, 'seller/manage_products.html', {
        'products': products, 
        'store': user_store,
        'out_of_stock_count': products.filter(stock_quantity=0).count(), 
        'total_earnings': total_earnings, 
        'total_items_sold': total_items_sold, 
        'reservations': active_claims,
        'pending_orders': pending_standard_orders, # <--- THIS MUST MATCH THE HTML KEY
    })
    
class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    # This allows the terminal to send 'user' as an ID

@login_required(login_url='login')
def create_store(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.is_seller:
        messages.error(request, "Denied. You are not registered as a seller.")
        return redirect('user_profile')
        
    if request.method == 'POST':
        store_name = request.POST.get('store_name')
        if store_name:
            Store.objects.create(user=request.user, store_name=store_name)
            messages.success(request, "🎉 Tindahan naidagdag!")
            return redirect('manage_products')
    return render(request, 'seller/create_store.html')

@login_required(login_url='login')
def create_product(request):
    user_store = Store.objects.filter(user=request.user).first()
    if not user_store: return redirect('user_profile')
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        cat_id = request.POST.get('category')
        new_cat = request.POST.get('new_category_name')
        if name and price:
            category = Category.objects.get_or_create(category_name=new_cat)[0] if new_cat else get_object_or_404(Category, id=cat_id)
            Product.objects.create(
                store=user_store, category=category, name=name, price=price,
                description=request.POST.get('description', ''),
                stock_quantity=request.POST.get('stock_quantity', 1),
                image=request.FILES.get('image'), status='Active'
            )
            messages.success(request, f"🛒 {name} naidagdag!")
            return redirect('manage_products') 
    return render(request, 'seller/create_product.html', {'categories': Category.objects.all()})

@login_required(login_url='login')
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, store__user=request.user)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock_quantity = request.POST.get('stock_quantity')
        product.description = request.POST.get('description')
        cat_id = request.POST.get('category')
        new_cat = request.POST.get('new_category_name')
        product.category = Category.objects.get_or_create(category_name=new_cat)[0] if new_cat else Category.objects.get(id=cat_id)
        if 'image' in request.FILES: product.image = request.FILES['image']
        product.save()
        messages.success(request, "Na-update!")
        return redirect('manage_products')
    return render(request, 'seller/edit_product.html', {'product': product, 'categories': Category.objects.all()})

@login_required(login_url='login')
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, store__user=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Nabura!")
    return redirect('manage_products')

@login_required(login_url='login')
def seller_orders(request):
    user_store = Store.objects.filter(user=request.user).first()
    if not user_store: return redirect('user_profile')
    orders = Order.objects.filter(items__product__store=user_store).distinct().order_by('-order_date')
    return render(request, 'seller/store_orders.html', {'orders': orders, 'store': user_store})

@login_required(login_url='login')
def seller_message_center(request):
    user_stores = Store.objects.filter(user=request.user)
    unique_customers = ChatMessage.objects.filter(store__in=user_stores).values('sender', 'sender__username', 'store__store_name').distinct()
    return render(request, 'seller/message_center.html', {'customers': unique_customers, 'stores': user_stores})

# ─────────────────────────────────────────
#   RESERVATION / CLAIM SYSTEM LOGIC
# ─────────────────────────────────────────

@login_required(login_url='login')
def reserve_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    qty = int(request.POST.get('quantity', 1))
    
    if product.stock_quantity >= qty:
        with transaction.atomic():
            # Calculate exactly 12 hours from right now
            expiry_time = timezone.now() + datetime.timedelta(hours=12)
            
            Reservation.objects.create(
                buyer=request.user, 
                product=product, 
                quantity=qty,
                expires_at=expiry_time,
                status='Active'
            )
            product.stock_quantity -= qty
            product.save()
            messages.success(request, "Surplus Claimed! Check your pickup timer in your History.")
    else:
        messages.error(request, "Not enough stock available for reservation.")
    
    return redirect('purchase_history')

@login_required(login_url='login')
def complete_reservation(request, res_id):
    res = get_object_or_404(Reservation, id=res_id, product__store__user=request.user)
    res.status = 'Completed'
    res.save()
    messages.success(request, "Claim marked as picked up.")
    return redirect('manage_products')


@login_required(login_url='login')
def reserve_checkout(request, pk):
    """Loads the dedicated Reservation Page for a buyer."""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'orders/reserve.html', {'product': product})

# ─────────────────────────────────────────
#   BUYER LOGIC & RESTRICTIONS
# ─────────────────────────────────────────

@login_required(login_url='login')
def checkout_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.user.is_superuser or profile.is_seller:
        messages.error(request, "Denied. Sellers and Admins cannot purchase.")
        return redirect('home')
        
    product_id = request.GET.get('product_id')
    qty = int(request.GET.get('quantity', 1)) if request.GET.get('quantity') else 1
    address = Address.objects.filter(user=request.user, is_default=True).first()
    
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        items = [{'product': product, 'quantity': qty, 'item_total': product.price * qty}]
        subtotal = product.price * qty
    else:
        cart_items = CartItem.objects.filter(cart__user=request.user)
        items = cart_items
        subtotal = sum((item.quantity * item.product.price for item in items), Decimal('0.00'))
        
    shipping, protect = Decimal('115.00'), Decimal('4.00')
    return render(request, 'orders/checkout.html', {
        'items': items, 'address': address, 'subtotal': subtotal,
        'protection': protect, 'shipping_fee': shipping, 'total_payment': subtotal + shipping + protect
    })

@login_required(login_url='login')
def view_cart(request):
    items = CartItem.objects.filter(cart__user=request.user).order_by('product__store__store_name')
    cart_total = sum((i.product.price * i.quantity for i in items), Decimal('0.00'))
    return render(request, 'cart.html', {'cart_items': items, 'cart_total': cart_total})

@login_required(login_url='login')
def add_address(request):
    if request.method == 'POST':
        Address.objects.filter(user=request.user).update(is_default=False)
        Address.objects.create(
            user=request.user, full_name=request.POST.get('full_name'), street=request.POST.get('street'),
            city=request.POST.get('city'), province=request.POST.get('province'),
            zip_code=request.POST.get('zip_code'), is_default=True
        )
        return redirect(request.META.get('HTTP_REFERER', 'user_profile'))
    return redirect('user_profile')

@login_required(login_url='login')
def purchase_history(request, pk=None):
    if pk:
        order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk, user=request.user)
        return render(request, 'orders/OrderDetail.html', {'order': order})
        
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    # Passing active_claims to render in the 'To Pickup' tab
    active_claims = Reservation.objects.filter(buyer=request.user, status='Active')
    
    return render(request, 'orders/PurchaseHistory.html', {
        'orders': orders,
        'active_claims': active_claims
    })

@login_required(login_url='login')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'orders/product_detail.html', {'product': product})

@login_required(login_url='login')
def checkout_pay(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/checkout.html', {
        'order': order, 'items': order.items.all(), 'address': order.address,
        'subtotal': order.total_amount - Decimal('119.00'), 
        'shipping_fee': Decimal('115.00'), 
        'protection': Decimal('4.00'), 
        'total_payment': order.total_amount
    })

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    # A helper function to safely attach the right Store and Category
    def _fix_store_and_category(self, instance, raw_store, raw_category):
        # Fix Store
        if raw_store:
            if str(raw_store).isdigit():
                instance.store_id = int(raw_store)
            else:
                store_obj = Store.objects.filter(store_name=str(raw_store)).first()
                if store_obj: 
                    instance.store = store_obj

        # Fix Category
        if raw_category:
            if str(raw_category).isdigit():
                instance.category_id = int(raw_category)
            else:
                cat_obj = Category.objects.filter(category_name=str(raw_category)).first()
                if cat_obj: 
                    instance.category = cat_obj
                    
        instance.save() # Commit to database

    # Intercept EDIT/SAVE requests (PATCH/PUT)
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 1. Copy the incoming data so we can modify it
        data = request.data.copy()
        
        # 2. PHYSICALLY DELETE the text strings so the Serializer doesn't crash
        # (Handles both standard dictionaries and locked QueryDicts)
        raw_store = data.pop('store', [None])[0] if isinstance(data.get('store'), list) else data.pop('store', None)
        raw_category = data.pop('category', [None])[0] if isinstance(data.get('category'), list) else data.pop('category', None)

        # 3. Let the Serializer save the normal stuff (Name, Price, Image)
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 4. Manually assign the Store and Category behind the Serializer's back
        self._fix_store_and_category(instance, raw_store, raw_category)
        
        return Response(serializer.data)

    # Intercept NEW requests (POST) just in case you create new products
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        raw_store = data.pop('store', [None])[0] if isinstance(data.get('store'), list) else data.pop('store', None)
        raw_category = data.pop('category', [None])[0] if isinstance(data.get('category'), list) else data.pop('category', None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        self._fix_store_and_category(instance, raw_store, raw_category)
        
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return Order.objects.all().order_by('-order_date')
        return Order.objects.filter(user=user).order_by('-order_date')
        
    def create(self, request, *args, **kwargs):
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        
        # 1. Restriction Check
        if user.is_superuser or profile.is_seller:
            return Response({"error": "Sellers and Admins are restricted from ordering."}, status=status.HTTP_403_FORBIDDEN)
            
        data = request.data
        product_id = data.get('product_id') or data.get('product')
        voucher_code = data.get('voucher_code') # <--- Get the code from your Checkout JS
        
        items_to_process = []
        calculated_subtotal = Decimal('0.00')
        
        # 2. Address Handling
        user_address = Address.objects.filter(user=user, is_default=True).first()
        formatted_address = f"{user_address.street}, {user_address.city}" if user_address else data.get('shipping_address', 'Default Address')
        
        # 3. Item Selection (Direct Buy vs Cart)
        if product_id:
            prod = get_object_or_404(Product, id=product_id)
            qty = int(data.get('quantity', 1))
            items_to_process.append({'product': prod, 'quantity': qty, 'price': prod.price})
            calculated_subtotal = prod.price * qty
        else:
            cart_items = CartItem.objects.filter(cart__user=user)
            if not cart_items.exists(): 
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            for item in cart_items:
                items_to_process.append({'product': item.product, 'quantity': item.quantity, 'price': item.product.price})
                calculated_subtotal += item.product.price * item.quantity
                
        try:
            with transaction.atomic():
                # 4. CREATE THE ORDER
                # We start with subtotal + standard fees
                order = Order.objects.create(
                    user=user, 
                    total_amount=calculated_subtotal + Decimal('119.00'), 
                    status='Pending',
                    payment_method=data.get('payment_method', 'COD'), 
                    address=user_address, 
                    shipping_address=formatted_address
                )

                # 5. LINK VOUCHER (Automatic Logic)
                applied_voucher = None
                if voucher_code:
                    # Look for the code entered by the user
                    applied_voucher = Voucher.objects.filter(code=voucher_code).first()
                
                # Fallback for your demo: if no code but you want a discount applied anyway
                if not applied_voucher:
                    applied_voucher = Voucher.objects.filter(id=2).first()

                # 6. CREATE AUTOMATIC PAYMENT
                new_payment = Payment.objects.create(
                    user=user,
                    method=order.payment_method,
                    amount=order.total_amount,
                    voucher=applied_voucher,  # <--- Linked voucher here
                    status='Pending'
                )
                
                # Link Payment to Order and Save
                order.payment = new_payment
                order.save() # This triggers the update_total() math in your models

                # 7. CREATE ORDER ITEMS & REDUCE STOCK
                for item in items_to_process:
                    if item['product'].stock_quantity < item['quantity']: 
                        raise ValueError(f"Not enough stock for {item['product'].name}")
                        
                    OrderItem.objects.create(
                        order=order, 
                        product=item['product'], 
                        quantity=item['quantity'], 
                        price=item['price']
                    )
                    item['product'].stock_quantity -= item['quantity']
                    item['product'].save()
                    
                # 8. CLEANUP
                if not product_id: 
                    CartItem.objects.filter(cart__user=user).delete()
                    
            return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self): 
        return ChatMessage.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user)).order_by('timestamp')
        
    def perform_create(self, serializer): 
        serializer.save(sender=self.request.user)

@method_decorator(csrf_exempt, name='dispatch')
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self): 
        return CartItem.objects.filter(cart__user=self.request.user)
        
    def perform_create(self, serializer):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        if self.request.user.is_superuser or profile.is_seller:
            raise ValidationError("Restricted. Sellers cannot add items to cart.")
        serializer.save(cart=Cart.objects.get_or_create(user=self.request.user)[0])


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer 

@api_view(['POST'])
def validate_voucher(request):
    code = request.data.get('code')
    subtotal = float(request.data.get('subtotal', 0))
    
    try:
        voucher = Voucher.objects.get(code=code, start_date__lte=timezone.now(), end_date__gte=timezone.now())
        
        # Check minimum spend
        if voucher.min_spend and subtotal < voucher.min_spend:
            return Response({'valid': False, 'message': f'Min spend ₱{voucher.min_spend} required.'}, status=400)
        
        # Calculate Discount
        if voucher.discount_type == 'percentage':
            discount_amount = subtotal * (float(voucher.discount_value) / 100)
        else:
            discount_amount = float(voucher.discount_value)

        return Response({
            'valid': True,
            'code': voucher.code,
            'discount_amount': discount_amount
        })
    except Voucher.DoesNotExist:
        return Response({'valid': False, 'message': 'Voucher not found or expired.'}, status=404)

class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['code'] # This allows the ?code= query
    
class UserViewSet(viewsets.ModelViewSet): queryset = User.objects.all(); serializer_class = UserSerializer
class CategoryViewSet(viewsets.ModelViewSet): queryset = Category.objects.all(); serializer_class = CategorySerializer
class StoreViewSet(viewsets.ModelViewSet): queryset = Store.objects.all(); serializer_class = StoreSerializer
class VoucherViewSet(viewsets.ModelViewSet): queryset = Voucher.objects.all(); serializer_class = VoucherSerializer
class ShipmentViewSet(viewsets.ModelViewSet): queryset = Shipment.objects.all(); serializer_class = ShipmentSerializer
class AddressViewSet(viewsets.ModelViewSet): queryset = Address.objects.all(); serializer_class = AddressSerializer
class PaymentViewSet(viewsets.ModelViewSet): queryset = Payment.objects.all(); serializer_class = PaymentSerializer
class CartViewSet(viewsets.ModelViewSet): queryset = Cart.objects.all(); serializer_class = CartSerializer
class ReviewViewSet(viewsets.ModelViewSet): queryset = Review.objects.all(); serializer_class = ReviewSerializer