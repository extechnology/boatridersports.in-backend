from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from Application.AuthenticationServices.auth_models import User
from Application.ProductServices.product_models import( 
    BikeModel,
    AccessoriesModel,
    SizeModel,
    BikeColorsModel
    )


class UserCartModel(models.Model):
    unique_id =  models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='user_carts')

    total_products = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    total_bikes = models.IntegerField(default=0)
    total_accessories = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username + " - " + str(self.total_products) + " - " + str(self.total_amount)


class UserCartItemsModelBike(models.Model):
    user_cart = models.ForeignKey(UserCartModel, on_delete=models.CASCADE,related_name='user_cart_bike_items')
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='user_cart_items')
    size = models.ForeignKey(SizeModel, on_delete=models.CASCADE,related_name='user_cart_items')
    color = models.ForeignKey(BikeColorsModel, on_delete=models.CASCADE,related_name='user_cart_items')
    quantity = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user_cart.user.username + " - " + self.bike.name + " - " + self.size.size + " - "

class UserCartItemsModelAccessories(models.Model):
    user_cart = models.ForeignKey(UserCartModel, on_delete=models.CASCADE,related_name='user_cart_accessory_items')
    accessory = models.ForeignKey(AccessoriesModel, on_delete=models.CASCADE,related_name='user_cart_items')
    quantity = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user_cart.user.username + " - " + self.accessory.name