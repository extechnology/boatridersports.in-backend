from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from Application.AuthenticationServices.auth_models import User

def generate_enquiry_id():
    return f"enquiry-{uuid.uuid4().hex[:8].upper()}"

class ContactEnquiryModel(models.Model):
    enquiry_id = models.CharField(max_length=255, default=generate_enquiry_id)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
