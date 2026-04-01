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
        model  = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'is_staff', 'is_active', 'date_joined']

        

# ==========================================
# CATALOG & STORE SERIALIZERS
# ==========================================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'parent']

class StoreSerializer(serializers.ModelSerializer):
    # Accept user as a plain numeric ID string from the admin terminal.
    # The default PrimaryKeyRelatedField already does this, but we make it
    # explicit and allow null so the serializer never crashes on a missing user.
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
 
    class Meta:
        model  = Store
        fields = '__all__'
 
    def validate_user(self, value):
        # value is already a User instance resolved by PrimaryKeyRelatedField.
        # If the terminal sent nothing, fall back to the request user.
        if value is None:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                return request.user
            raise serializers.ValidationError("A valid user is required.")
        return value

 
class ProductSerializer(serializers.ModelSerializer):
    # Accept a plain string name for category and store instead of a PK.
    # write_only=True so the field accepts input; we still return the name on read.
    category = serializers.CharField()   # accepts name string OR numeric id string
    store    = serializers.CharField(allow_blank=True, required=False, allow_null=True)
 
    class Meta:
        model  = Product
        fields = '__all__'
 
    # ── helpers ──────────────────────────────────────────────────────────────
 
    def _resolve_category(self, value):
        """Return a Category instance from a name string or numeric id."""
        if value is None:
            raise serializers.ValidationError("Category is required.")
        s = str(value).strip()
        if s.isdigit():
            try:
                return Category.objects.get(pk=int(s))
            except Category.DoesNotExist:
                raise serializers.ValidationError(f"Category id {s} not found.")
        obj = Category.objects.filter(category_name__iexact=s).first()
        if not obj:
            raise serializers.ValidationError(f"Category '{s}' not found.")
        return obj
 
    def _resolve_store(self, value):
        """Return a Store instance from a name string or numeric id (nullable)."""
        if value is None or str(value).strip() == '':
            return None
        s = str(value).strip()
        if s.isdigit():
            try:
                return Store.objects.get(pk=int(s))
            except Store.DoesNotExist:
                raise serializers.ValidationError(f"Store id {s} not found.")
        obj = Store.objects.filter(store_name__iexact=s).first()
        if not obj:
            raise serializers.ValidationError(f"Store '{s}' not found.")
        return obj
 
    # ── validation ────────────────────────────────────────────────────────────
 
    def validate_category(self, value):
        return self._resolve_category(value)   # returns Category instance
 
    def validate_store(self, value):
        return self._resolve_store(value)       # returns Store instance or None
 
    # ── create / update ───────────────────────────────────────────────────────
 
    def create(self, validated_data):
        # validated_data already has real Category/Store instances thanks to validate_*
        return Product.objects.create(**validated_data)
 
    def update(self, instance, validated_data):
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance
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