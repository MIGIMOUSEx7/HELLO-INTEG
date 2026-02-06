from django.contrib import admin
from .models import (
    Address, Category, Product, Store, 
    Voucher, Shipment, Payment, Order, Cart, CartItem
)

# NOTE: We do NOT import or register 'User' here because
# Django's built-in Auth system already registers it for you.

# 1. Product Admin with Bulk Restock
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ('name', 'category', 'price', 'stock_quantity', 'status')
    list_filter = ('category', 'status') # Sidebar filters
    search_fields = ('name',)
    
    # Custom Restock Action
    actions = ['restock_to_twenty']

    @admin.action(description='Restock selected items to 20 units')
    def restock_to_twenty(self, request, queryset):
        # Directly updates MySQL in one query
        updated = queryset.update(stock_quantity=20)
        self.message_user(request, f"Successfully restocked {updated} products.")

# 2. Order Admin to track your Shopee sales
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'order_date')
    list_editable = ('status',) # Allows changing status without clicking the order
    list_filter = ('status', 'order_date')

# 3. Simple registration for the remaining ERD tables
admin.site.register(Address)
admin.site.register(Category)
admin.site.register(Store)
admin.site.register(Voucher)
admin.site.register(Shipment)
admin.site.register(Payment)
admin.site.register(Cart)
admin.site.register(CartItem)