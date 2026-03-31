from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Cart, CartItem, Product, Order, OrderItem,
    Category, Store, Voucher, Shipment, Address,
    Payment, Review, ChatMessage, Reservation, Profile
)

# ==========================================
# USER & PROFILE SERIALIZERS
# ==========================================
class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Profile
        fields = ['id', 'user', 'username', 'phone_number', 'profile_picture', 'bio', 'is_seller']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

# ==========================================
# CATALOG & STORE SERIALIZERS
# ==========================================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'parent']

class StoreSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Store
        fields = ['id', 'user', 'owner_name', 'store_name', 'store_description', 'rating', 'profile_picture', 'banner_image', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    store_name = serializers.ReadOnlyField(source='store.store_name')
    category_name = serializers.ReadOnlyField(source='category.category_name')
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'store', 'store_name', 'category', 'category_name', 
            'name', 'description', 'price', 'stock_quantity', 
            'status', 'is_surplus', 'image', 'created_at'
        ]

# ==========================================
# TRANSACTIONAL SERIALIZERS
# ==========================================
class ReservationSerializer(serializers.ModelSerializer):
    buyer_name = serializers.ReadOnlyField(source='buyer.username')
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = Reservation
        fields = [
            'id', 'buyer', 'buyer_name', 
            'product', 'product_name', 
            'quantity', 'status', 'created_at', 'expires_at'
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    items = OrderItemSerializer(many=True, read_only=True)
    formatted_date = serializers.SerializerMethodField()
    
    # FIX: Explicitly allow the payment ID to be sent and saved
    payment = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.all(), 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_name', 'payment', 'items', 
            'total_amount', 'status', 'order_date', 
            'formatted_date', 'payment_method', 'shipping_address'
        ]

    def get_formatted_date(self, obj):
        return obj.order_date.strftime("%b %d, %Y") if obj.order_date else None

# ==========================================
# LOGISTICS & UTILITY SERIALIZERS
# ==========================================
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    receiver_name = serializers.ReadOnlyField(source='receiver.username')

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'sender_name', 'receiver', 'receiver_name', 'store', 'message', 'timestamp', 'is_read']

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_name', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at', 'updated_at']

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Review
        fields = ['id', 'order', 'user', 'username', 'product', 'rating', 'comment', 'created_at']