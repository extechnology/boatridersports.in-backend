from django.contrib import admin
from .profile_models import UserProfile, UserAddress

admin.site.register(UserProfile)
admin.site.register(UserAddress)