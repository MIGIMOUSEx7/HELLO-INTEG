from django.contrib import admin
from .models import (
    Address, Category, Product, Store, 
    Voucher, Shipment, Payment, Order, OrderItem,
    Cart, CartItem, ChatMessage
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'status')
    list_filter = ('category', 'status')
    search_fields = ('name',)
    actions = ['restock_to_twenty']

    @admin.action(description='Restock selected items to 20 units')
    def restock_to_twenty(self, request, queryset):
        updated = queryset.update(stock_quantity=20)
        self.message_user(request, f"Successfully restocked {updated} products.")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'order_date')
    list_editable = ('status',)
    list_filter = ('status', 'order_date')
    inlines = [OrderItemInline]

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'store', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read', 'store')
    search_fields = ('message', 'sender__username', 'receiver__username')

admin.site.register(Address)
admin.site.register(Category)
admin.site.register(Store)
admin.site.register(Voucher)
admin.site.register(Shipment)
admin.site.register(Payment)
admin.site.register(Cart)
admin.site.register(CartItem)