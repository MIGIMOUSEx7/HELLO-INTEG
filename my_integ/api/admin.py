from django.contrib import admin
from .models import User, Address, Category, Product, Store, Voucher, Shipment, Payment, Order, Cart, CartItem

# Registering all models from your ERD
my_models = [User, Address, Category, Product, Store, Voucher, Shipment, Payment, Order, Cart, CartItem]
admin.site.register(my_models)