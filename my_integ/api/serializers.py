from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    Cart, CartItem, Product, Order, OrderItem,
    Category, Store, Voucher, Shipment, Address,
    Payment, Review, ChatMessage, Reservation
)

# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


# ─────────────────────────────────────────
# RESERVATION
# ─────────────────────────────────────────
class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'


# ─────────────────────────────────────────
# BASIC MODELS
# ─────────────────────────────────────────
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


# ─────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────
class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    receiver_name = serializers.ReadOnlyField(source='receiver.username')

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'sender_name',
            'receiver', 'receiver_name',
            'store', 'message',
            'timestamp', 'is_read'
        ]
        read_only_fields = ['sender']


# ─────────────────────────────────────────
# PRODUCT
# ─────────────────────────────────────────
class ProductSerializer(serializers.ModelSerializer):
    # Lookup 'store_name' from the related Store model
    store = serializers.SlugRelatedField(
        slug_field='store_name', 
        queryset=Store.objects.all()
    )
    # Lookup 'category_name' from the related Category model
    category = serializers.SlugRelatedField(
        slug_field='category_name', 
        queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = '__all__'


# ─────────────────────────────────────────
# ORDER ITEMS
# ─────────────────────────────────────────
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']


# ─────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    formatted_date = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'email', 'items',
            'total_amount', 'status',
            'order_date', 'formatted_date',
            'payment_method', 'shipping_address',
            'shipment', 'address', 'payment'
        ]

    def get_formatted_date(self, obj):
        return obj.order_date.strftime("%b %d, %Y")


# ─────────────────────────────────────────
# CART
# ─────────────────────────────────────────
class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['product'] = ProductSerializer(instance.product).data
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items']


# ─────────────────────────────────────────
# REVIEW
# ─────────────────────────────────────────
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'order', 'product', 'rating', 'comment']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)