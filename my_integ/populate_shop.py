import os
import django
import random

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_integ.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Category, Store, Product, Cart, Address, Order, OrderItem, Payment, CartItem

def populate():
    print("🔄 Cleaning old data...")
    
    # CRITICAL FIX: Delete child records first to avoid ProtectedError
    print("   - Deleting Order Items...")
    OrderItem.objects.all().delete()
    
    print("   - Deleting Orders...")
    Order.objects.all().delete()

    print("   - Deleting Cart Items...")
    CartItem.objects.all().delete()

    print("   - Deleting Carts...")
    Cart.objects.all().delete()

    print("   - Deleting Products...")
    Product.objects.all().delete()

    print("   - Deleting Stores...")
    Store.objects.all().delete()

    print("   - Deleting Addresses...")
    Address.objects.all().delete()

    print("   - Deleting Payments...")
    Payment.objects.all().delete()

    print("   - Deleting Categories...")
    Category.objects.all().delete()
    
    print("   - Deleting Users (except superusers)...")
    User.objects.exclude(is_superuser=True).delete()
    
    print("---------------------------------------")
    print("👤 Creating Users...")
    # Create standard users from your screenshots
    user_first = User.objects.create_user(username='firstuser', email='first@email.com', password='password123')
    user_shop = User.objects.create_user(username='shop_owner', email='shop@email.com', password='password123')
    user_van = User.objects.create_user(username='vanelectro', email='van@email.com', password='password123')
    user_mercy = User.objects.create_user(username='mercy', email='mercy@email.com', password='password123')

    # Create Carts for them
    Cart.objects.get_or_create(user=user_first)

    # Create a default address for the buyer
    Address.objects.create(
        user=user_first,
        full_name="First User",
        phone="09123456789",
        street="123 Sampaguita St",
        city="Manila",
        province="Metro Manila",
        zip_code="1000",
        country="Philippines",
        is_default=True
    )

    print("📂 Creating Categories...")
    cat_necessity = Category.objects.create(category_name="Necessity")
    cat_meds = Category.objects.create(category_name="Medication")
    cat_electro = Category.objects.create(category_name="Electronics")

    print("🏪 Creating Stores...")
    store_sari = Store.objects.create(user=user_shop, store_name="Shop SariSariStore", rating=4.5)
    store_mercy = Store.objects.create(user=user_mercy, store_name="MerciyDragstoere", rating=4.8)
    store_van = Store.objects.create(user=user_van, store_name="VAN ELECTRO", rating=5.0)

    print("📦 Creating Products...")
    
    # Products for Shop SariSariStore (Necessity)
    Product.objects.create(
        store=store_sari,
        category=cat_necessity,
        name="totpaste",
        description="Daily toothpaste",
        price=25.00,
        stock_quantity=20,
        status="Available"
    )
    Product.objects.create(
        store=store_sari,
        category=cat_necessity,
        name="Napkin",
        description="Hygiene product",
        price=20.00,
        stock_quantity=50,
        status="Available"
    )

    # Products for MerciyDragstoere (Medication)
    Product.objects.create(
        store=store_mercy,
        category=cat_meds,
        name="bioflu",
        description="For flu relief",
        price=15.00,
        stock_quantity=97,
        status="Available"
    )
    Product.objects.create(
        store=store_mercy,
        category=cat_meds,
        name="Paracetamol",
        description="For headache",
        price=15.00,
        stock_quantity=98,
        status="Available"
    )

    # Products for VAN ELECTRO (Electronics)
    Product.objects.create(
        store=store_van,
        category=cat_electro,
        name="PSU",
        description="Power Supply Unit 600W",
        price=3500.00,
        stock_quantity=15,
        status="Available"
    )
    Product.objects.create(
        store=store_van,
        category=cat_electro,
        name="MotherBoard",
        description="B450M Gaming Motherboard",
        price=5500.00,
        stock_quantity=15,
        status="Available"
    )

    print("✅ Database Populated Successfully!")

if __name__ == '__main__':
    populate()