from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.contrib import admin
from Application.AuthenticationServices.auth_models import User
from .usercart_models import UserCartModel, UserCartItemsModelBike, UserCartItemsModelAccessories


admin.site.register(UserCartModel)
admin.site.register(UserCartItemsModelBike)
admin.site.register(UserCartItemsModelAccessories)