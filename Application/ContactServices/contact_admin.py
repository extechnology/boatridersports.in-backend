from django.contrib import admin
from .contact_models import ContactEnquiryModel
@admin.register(ContactEnquiryModel)
class ConatactEnquiryModelAdmin(admin.ModelAdmin):
    list_display = ['enquiry_id', 'name', 'email', 'phone', 'created']
    list_filter = ['created']
    search_fields = ['enquiry_id', 'name', 'email', 'phone']
