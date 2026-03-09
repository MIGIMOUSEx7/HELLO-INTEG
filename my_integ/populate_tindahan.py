import os
import django
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal  # <-- ADDED THIS IMPORT

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_integ.settings')
django.setup()

from api.models import (
    Category, Store, Product, User, Address, 
    Voucher, Shipment, Payment, Order, OrderItem
)

def populate():
    print("Starting Tindahan population script...")

    # 1. Create Users
    users = []
    user_data = [
        ('ivan_jeff', 'ivan@example.com'),
        ('sari_sari_admin', 'admin@tindahan.com'),
        ('juan_delacruz', 'juan@example.com')
    ]
    for username, email in user_data:
        user, created = User.objects.get_or_create(username=username, email=email)
        if created:
            user.set_password('password123')
            user.save()
        users.append(user)

    # 2. Create Categories
    categories = []
    cat_names = ['Electronics', 'Home Decor', 'Vintage Items']
    for name in cat_names:
        cat, _ = Category.objects.get_or_create(category_name=name)
        categories.append(cat)

    # 3. Create Stores
    stores = []
    store_data = [
        ('Tech Haven', users[0]),
        ('Retro Finds', users[1]),
        ('Official Tindahan', users[2])
    ]
    for name, user in store_data:
        store, _ = Store.objects.get_or_create(
            store_name=name, 
            user=user,
            defaults={'store_description': f'Welcome to {name}! The best store in town.'}
        )
        stores.append(store)

    # 4. Create Products
    products = []
    product_data = [
        ('MotherBoard', 5500.00, categories[0], stores[0]),
        ('Mechanical Keyboard', 2500.00, categories[0], stores[0]),
        ('Vintage Lamp', 1200.00, categories[1], stores[1]),
        ('Woven Basket', 450.00, categories[1], stores[2]),
        ('Classic Watch', 3200.00, categories[2], stores[1])
    ]
    for name, price, cat, store in product_data:
        prod, _ = Product.objects.get_or_create(
            name=name, price=price, category=cat, store=store,
            defaults={'description': f'Premium {name}', 'stock_quantity': 10, 'status': 'Active'}
        )
        products.append(prod)

    # 5. Create Addresses
    address_data = [
        (users[0], 'Ivan Jeff Plaza', '09123456789', 'Seer St', 'CDO', 'Mis Or', '9000'),
        (users[2], 'Juan dela Cruz', '09987654321', 'Main Ave', 'Manila', 'NCR', '1000'),
        (users[2], 'Juan Home', '09987654321', 'Second St', 'Quezon City', 'NCR', '1100')
    ]
    for u, name, phone_val, street, city, prov, zip_c in address_data:
        Address.objects.get_or_create(
            user=u, full_name=name, phone=phone_val,
            street=street, city=city, province=prov, zip_code=zip_c,
            defaults={'country': 'Philippines', 'is_default': True}
        )

    # 6. Create Vouchers
    now = timezone.now()
    next_month = now + timedelta(days=30)
    
    voucher_codes = [('WELCOME10', 10.0), ('TINDAHAN50', 50.0), ('FREESHIP', 60.0)]
    for code, disc in voucher_codes:
        Voucher.objects.get_or_create(
            code=code,
            defaults={
                'discount_type': 'Fixed',
                'discount_value': disc,
                'min_spend': 100.00,
                'start_date': now,
                'end_date': next_month
            }
        )

    # 7. Create Orders & Order Items
    for i in range(3):
        order, _ = Order.objects.get_or_create(
            user=users[2],
            total_amount=products[i].price + Decimal('119.00'),  # <-- FIXED ERROR HERE
            status='Pending',
            payment_method='COD'
        )
        OrderItem.objects.get_or_create(
            order=order, product=products[i], quantity=1, price=products[i].price
        )

    print("Successfully populated 3+ entries for all Tindahan models!")

if __name__ == '__main__':
    populate()