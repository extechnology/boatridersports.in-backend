from rest_framework import serializers
from .contact_models import ContactEnquiryModel

class ContactEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactEnquiryModel
        fields = ['enquiry_id', 'name', 'email', 'phone', 'subject', 'message', 'created', 'updated']