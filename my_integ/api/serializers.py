from rest_framework import serializers
from .models import (Product, Order, User, Category, Store, 
                      Voucher, Shipment, Address, Payment)

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
    class Meta:
        model = Product
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    # Relational enhancements: Pulling real-time data across tables
    user_full_name = serializers.ReadOnlyField(source='user.first_name')
    user_last_name = serializers.ReadOnlyField(source='user.last_name')
    
    # Method to check shipment status dynamically
    shipment_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        # Adding relational fields to the standard order output
        fields = [
            'id', 'user', 'user_full_name', 'user_last_name', 
            'address', 'payment', 'status', 'total_amount', 
            'shipment_status'
        ]

    def get_shipment_status(self, obj):
        # Look up shipment record for this specific order
        shipment = Shipment.objects.filter(order=obj).first()
        return shipment.status if shipment else "Not Shipped Yet"