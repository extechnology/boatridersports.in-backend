from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from Application.ProductServices.product_models import BikeModel, AccessoriesModel, BikeColorsModel, BikeSizesModel, SizeModel
from Application.ProfileServices.profile_models import UserAddress
from Application.AuthenticationServices.auth_models import User

def generate_order_id():
    return f"order-{uuid.uuid4()}"


class UserOrdersModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='orders')
    
    user_address = models.ForeignKey(UserAddress, on_delete=models.CASCADE,related_name='orders')
    unique_id = models.CharField(max_length=50, unique=True, default=generate_order_id, editable=False)
    
    ORDER_STATUS = (
        ('Pending','Pending'),
        ('Processing','Processing'),
        ('Shipped','Shipped'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled'),
        ('Failed','Failed')
    )
    status = models.CharField(max_length=50,choices=ORDER_STATUS,default='Pending')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_items = models.IntegerField(default=0)
    payment_status = models.BooleanField(default=False)

    invoice = models.FileField(upload_to='invoices/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    deliverd_at = models.DateTimeField(null=True, blank=True)
    tracking_id = models.CharField(max_length=200, null=True, blank=True)
    shipped_via = models.CharField(max_length=200, null=True, blank=True)
    

    def __str__(self):
        return self.unique_id


class BikeOrderItems(models.Model):
    order = models.ForeignKey(UserOrdersModel, on_delete=models.CASCADE,related_name='bike_orders')
    
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='bike_orders',null=True,blank=True)
    color = models.ForeignKey(BikeColorsModel, on_delete=models.CASCADE,related_name='bike_orders',null=True,blank=True)
    size = models.ForeignKey(SizeModel, on_delete=models.CASCADE,related_name='bike_orders',null=True,blank=True)
    
    quantity = models.IntegerField(default=1)
     
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.unique_id} - Bike"

class AccessoriesOrderItems(models.Model):
    order = models.ForeignKey(UserOrdersModel, on_delete=models.CASCADE,related_name='accessories_orders')
    
    accessory = models.ForeignKey(AccessoriesModel, on_delete=models.CASCADE,related_name='accessories_orders',null=True,blank=True)
    
    quantity = models.IntegerField(default=1)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.unique_id} - Accessory"
