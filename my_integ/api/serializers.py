from rest_framework import serializers
from .models import (
    Cart, CartItem, Product, Order, User, Category, Store, 
    Voucher, Shipment, Address, Payment
)

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

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    # Explicitly including stock_quantity for the "Sold Out" logic
    class Meta:
        model = Product
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    # Pulling User details for the "van plaza" display
    user_full_name = serializers.ReadOnlyField(source='user.first_name')
    user_last_name = serializers.ReadOnlyField(source='user.last_name')
    shipment_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_full_name', 'user_last_name', 
            'address', 'payment', 'status', 'total_amount', 
            'shipment_status'
        ]

    def get_shipment_status(self, obj):
        # Checks the api_shipment table for linked orders
        shipment = Shipment.objects.filter(status=obj.status).first() 
        return shipment.status if shipment else "Pending Approval"

# --- New Cart Serializers ---

class CartItemSerializer(serializers.ModelSerializer):
    # Helpful for displaying product names in the cart view
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.price')

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_name', 'product_price', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    # This allows you to see all items inside a cart in one API call
    items = CartItemSerializer(many=True, read_only=True, source='cartitem_set')

    class Meta:
        model = Cart
        fields = ['id', 'store', 'created_at', 'items']