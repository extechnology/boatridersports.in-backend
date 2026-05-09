from Application.AuthenticationServices.auth_models import User
import uuid
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='user_profile')
    name = models.CharField(max_length = 200,null=True,blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures', blank=True, null=True)
    phone_number = models.CharField(max_length=15,null=True,blank=True)
    email = models.EmailField(max_length=200, unique = True,null=True,blank=True)
    date_of_birth = models.DateField(null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = self.phone_number.strip()
            if self.phone_number.startswith('+91'):
                self.phone_number = self.phone_number[3:].strip()
        super().save(*args, **kwargs)
        
class UserAddress(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='user_addresses')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
    address_type = models.CharField(max_length=10,null=True,blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    is_default = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username + " - " + self.name

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = self.phone_number.strip()
            if self.phone_number.startswith('+91'):
                self.phone_number = self.phone_number[3:].strip()
        super().save(*args, **kwargs)