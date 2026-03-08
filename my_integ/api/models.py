from django.db import models
from django.contrib.auth.models import User

class Address(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}"

class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name_plural = "Categories"

class Store(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    store_name = models.CharField(max_length=100)
    store_description = models.TextField()
    rating = models.FloatField(default=0.0)
    
    profile_picture = models.ImageField(upload_to='stores/profiles/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='stores/banners/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name

class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)
    stock_quantity = models.IntegerField(default=20) 
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, default="Active")
    image = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} (Stock: {self.stock_quantity})"

class Voucher(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=100)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.code

class Shipment(models.Model):
    id = models.BigAutoField(primary_key=True)
    courier = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    return_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.courier} - {self.tracking_number}"

class Payment(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    method = models.CharField(max_length=100)
    voucher = models.ForeignKey(Voucher, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method}: {self.amount}"

class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    address = models.ForeignKey(Address, on_delete=models.PROTECT, null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, null=True, blank=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=50, default="COD")
    shipping_address = models.TextField(default="Default Address")
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, default="Pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Cart(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"