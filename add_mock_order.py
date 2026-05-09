import os
import django
import sys

# Add project path to sys.path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BotRiderProject.settings')
django.setup()

from Application.OrderServices.order_models import UserOrdersModel, BikeOrderItems, AccessoriesOrderItems
from Application.ProductServices.product_models import BikeModel, AccessoriesModel
from Application.ProfileServices.profile_models import UserAddress
from Application.AuthenticationServices.auth_models import User

def add_mock_order():
    user = User.objects.first()
    if not user:
        print("No users found in database.")
        return

    address = UserAddress.objects.filter(user=user).first()
    if not address:
        address = UserAddress.objects.create(
            user=user,
            name="Mock Address",
            phone_number="1234567890",
            address="123 Main St",
            city="Test City",
            state="Test State",
            pincode="123456"
        )

    order = UserOrdersModel.objects.create(
        user=user,
        user_address=address,
        status="Pending",
        total_amount=0,
        total_items=0
    )

    total_amount = 0
    total_items = 0

    from Application.ProductServices.product_models import BikeColorsModel, SizeModel

    bike = BikeModel.objects.first()
    if bike:
        color = BikeColorsModel.objects.first()
        size = SizeModel.objects.first()

        BikeOrderItems.objects.create(
            order=order,
            bike=bike,
            color=color,
            size=size,
            quantity=1,
            price=bike.price,
            subtotal=bike.price
        )
        total_amount += float(bike.price)
        total_items += 1
        print(f"Added bike to order with color '{color.color.color_name if color and color.color else 'None'}' and size '{size.size if size else 'None'}'.")

    accessory = AccessoriesModel.objects.first()
    if accessory:
        AccessoriesOrderItems.objects.create(
            order=order,
            accessory=accessory,
            quantity=1,
            price=accessory.price,
            subtotal=accessory.price
        )
        total_amount += float(accessory.price)
        total_items += 1
        print("Added accessory to order.")

    order.total_amount = total_amount
    order.total_items = total_items
    order.save()

    print(f"Successfully created order: {order.unique_id}")

if __name__ == '__main__':
    add_mock_order()
