from django.contrib import admin
from .ui_models import *

class HomeSliderVideoAdmin(admin.ModelAdmin):
    # list_display = ('desktop_video', 'mobile_video', 'title', 'sub_title', 'description', 'created_at', 'updated_at')
    list_filter = ('desktop_video', 'mobile_video', 'title', 'sub_title', 'description', 'created_at', 'updated_at')
    search_fields = ('desktop_video', 'mobile_video', 'title', 'sub_title', 'description')
    ordering = ('-created_at',)

admin.site.register(HomeSliderVideoModel, HomeSliderVideoAdmin)