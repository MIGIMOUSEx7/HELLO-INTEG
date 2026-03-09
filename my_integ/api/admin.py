from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    Address, Category, Product, Store, 
    Voucher, Shipment, Payment, Order, OrderItem,
    Cart, CartItem, ChatMessage, Profile  # <-- Added Profile here
)
    
# --- 1. USER & PROFILE ADMIN SETUP ---
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Shop Owner Access (Profile)'

# Unregister the default User admin provided by Django
admin.site.unregister(User)

# Register the new User admin that includes our Profile inline checkbox
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


# --- 2. PRODUCT ADMIN ---
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


# --- 3. ORDER ADMIN ---
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


# --- 4. CHAT MESSAGE ADMIN ---
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'store', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read', 'store')
    search_fields = ('message', 'sender__username', 'receiver__username')


# --- 5. BASIC REGISTRATIONS ---
admin.site.register(Address)
admin.site.register(Category)
admin.site.register(Store)
admin.site.register(Voucher)
admin.site.register(Shipment)
admin.site.register(Payment)
admin.site.register(Cart)
admin.site.register(CartItem)