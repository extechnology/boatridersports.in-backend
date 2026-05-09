from django.urls import path
from .contact_views import ContactEnquiryViewDashboard


urlpatterns = [
    path('enquiries/', ContactEnquiryViewDashboard.as_view(), name='enquiries'),
]