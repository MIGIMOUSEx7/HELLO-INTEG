import os
import django
from decimal import Decimal
from datetime import timedelta # Correct import for time math
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_integ.settings')
django.setup()

from api.models import User, Category, Store, Product, Address, Payment, Voucher, Shipment, Order

def populate():
    print("🚀 Starting Extended Population...")

    # 1. Create User (van plaza)
    user, _ = User.objects.get_or_create(
        id=1,
        defaults={'first_name': 'van', 'last_name': 'plaza', 'email': 'ivan@gmail.com'}
    )

    # 2. Create Voucher
    voucher, _ = Voucher.objects.get_or_create(
        code="SAVE50",
        defaults={
            'discount_type': 'Fixed',
            'discount_value': Decimal('50.00'),
            'min_spend': Decimal('100.00'),
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30) # Fixed line
        }
    )

    # 3. Create Address
    addr, _ = Address.objects.get_or_create(id=1, user=user, defaults={'city': 'cdc', 'full_name': 'van'})

    # 4. Create Payment
    pay, _ = Payment.objects.get_or_create(
        id=1, 
        user=user, 
        defaults={
            'method': 'Cash g', 
            'amount': Decimal('1450.00'), 
            'voucher_id': voucher.id
        }
    )

    # 5. Create Product and Category
    cat, _ = Category.objects.get_or_create(category_name="Electronics")
    prod, _ = Product.objects.get_or_create(name="Shabs", defaults={'category': cat, 'status': 'Available'})

    # 6. Create initial Order
    order, _ = Order.objects.get_or_create(
        id=1,
        user=user,
        address=addr,
        payment=pay,
        defaults={'status': 'Processing', 'total_amount': Decimal('1450.00')}
    )

    # 7. Create Shipment
    Shipment.objects.get_or_create(
        order=order,
        defaults={
            'courier': 'J&T Express',
            'tracking_number': 'IVAN123456789',
            'status': 'In Transit',
            'shipped_at': timezone.now()
        }
    )

    print("✅ Full ERD Lifecycle Populated!")

if __name__ == '__main__':
    populate()