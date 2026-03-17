from rest_framework import serializers
from .models import (
    Cart, CartItem, Product, Order, OrderItem, User, Category, Store, 
    Voucher, Shipment, Address, Payment, Review, ChatMessage
)

class UserSerializer(serializers.ModelSerializer):

    address = serializers.CharField(source='profile.address', read_only=True)
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'address', 'phone_number']

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

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    receiver_name = serializers.ReadOnlyField(source='receiver.username')
    sender = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'sender_name', 'receiver', 
            'receiver_name', 'store', 'message', 'timestamp', 'is_read'
        ]

class ProductSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'

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

class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.product:
            representation['product'] = ProductSerializer(instance.product).data
        return representation

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'order', 'product', 'rating', 'comment']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)