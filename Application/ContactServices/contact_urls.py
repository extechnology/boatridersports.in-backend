from django.urls import path
from .contact_views import *

urlpatterns = [
    path('contact-enquiry/', ContactEnquiryView.as_view(), name='contact-enquiry'),
]