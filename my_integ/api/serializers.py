from rest_framework import serializers
from .models import (
    Cart, CartItem, Product, Order, OrderItem, User, Category, Store, 
    Voucher, Shipment, Address, Payment
)

# --- Basic Serializers ---

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

# --- Nested Serializers ---

class ProductSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'

# --- ORDER SYSTEM ---

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'items', 'total_amount', 'status', 
            'order_date', 'formatted_date', 'payment_method', 'shipping_address',
            'shipment', 'address', 'payment'
        ]

    def get_formatted_date(self, obj):
        return obj.order_date.strftime("%b %d, %Y")

# --- CART SYSTEM (FIXED) ---

class CartItemSerializer(serializers.ModelSerializer):
    # 1. WRITE: Expects an ID (e.g., "product": 5) from the frontend
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

    # 2. READ: Swaps the ID for the full Product Object (Image, Name, Price)
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Verify product exists before serializing to prevent crashes
        if instance.product:
            representation['product'] = ProductSerializer(instance.product).data
        return representation

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items']