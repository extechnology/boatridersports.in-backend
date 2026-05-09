from django.contrib import admin
from .order_models import *
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

class BikeOrderInline(NestedTabularInline):
    model = BikeOrderItems
    extra = 0
    readonly_fields = ('subtotal', 'price')

    def get_readonly_fields(self, request, obj=None):
        # Make all fields readonly after save
        if obj and obj.pk:
            return self.readonly_fields + ('bike', 'color', 'size', 'quantity', 'price', 'subtotal')
        return self.readonly_fields

class AccessoriesOrderInline(NestedTabularInline):
    model = AccessoriesOrderItems
    extra = 0
    readonly_fields = ('subtotal', 'price')

    def get_readonly_fields(self, request, obj=None):
        # Make all fields readonly after save
        if obj and obj.pk:
            return self.readonly_fields + ('accessory', 'quantity', 'price', 'subtotal')
        return self.readonly_fields


@admin.register(UserOrdersModel)
class UserOrdersModelAdmin(NestedModelAdmin):
    list_display = ('unique_id', 'user', 'user_address', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('unique_id', 'user__email', 'user__username', 'user_address__address_line_1')
    inlines = [BikeOrderInline, AccessoriesOrderInline]
    readonly_fields = ('unique_id', 'created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        # Make all fields readonly after save
        if obj and obj.pk:
            return self.readonly_fields + ('user', 'user_address')
        return self.readonly_fields

@admin.register(BikeOrderItems)
class BikeOrderItemsAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'bike', 'color', 'size', 'quantity', 'price', 'subtotal', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')  
    search_fields = ('id', 'order__unique_id', 'bike__name')

@admin.register(AccessoriesOrderItems)
class AccessoriesOrderItemsAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'accessory', 'quantity', 'price', 'subtotal', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('id', 'order__unique_id', 'accessory__name')