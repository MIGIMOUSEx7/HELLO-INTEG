from rest_framework import serializers
from .models import (
    Cart, CartItem, Product, Order, OrderItem, User, Category, Store, 
    Voucher, Shipment, Address, Payment, Review
)
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated 

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


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-order_date')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    # ... (existing create and partial_update methods) ...

    @action(detail=True, methods=['post'], url_path='submit-review')
    def submit_review(self, request, pk=None):
        order = self.get_object()
        
        # Kunin ang unang product sa order bilang default target ng review
        first_item = order.items.first()
        if not first_item:
            return Response({"error": "No items found in this order."}, status=status.HTTP_400_BAD_REQUEST)

        # I-prepare ang data para sa serializer
        review_data = {
            'order': order.id,
            'product': first_item.product.id,
            'rating': request.data.get('rating'),
            'comment': request.data.get('text') # 'text' ang key sa JS modal mo
        }

        serializer = ReviewSerializer(data=review_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# api/serializers.py

class ReviewSerializer(serializers.ModelSerializer): # <--- Siguraduhin ang spelling nito
    class Meta:
        model = Review
        fields = ['id', 'order', 'product', 'rating', 'comment']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)