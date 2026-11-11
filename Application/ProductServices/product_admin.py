from Application.ProductServices.product_models import ShippingChargeModel
import nested_admin
from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from .admin_file_preserver import PreserveFilesAdminMixin
from .admin_duplicator import clone_bike, clone_accessory
from .product_models import (
    BikeCategoryModel, BikeBrandModel, ColorModel, SizeModel, SpecialTagModel,
    BikeModel, BikeSizesModel, BikeColorsModel, BikeImagesModel,
    BikeSpecLabelModel, BikeSpecValueModel, BikePostersModel, BikeDownloadsModel,
    MaterialModel, SuspensionModel, WheelSizeModel, RearSuspensionTravelModel,
    AccessoriesCategoryModel, GuideAndTrainerModel, AccessoriesSubCategoryModel, 
    AccessoriesModel, BikeReviewsModel, AccessoryImagesModel
)

@admin.register(MaterialModel)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('material', 'created')
    list_filter = ('created',)
    search_fields = ('material',)

@admin.register(SuspensionModel)
class SuspensionAdmin(admin.ModelAdmin):
    list_display = ('suspension', 'created')
    list_filter = ('created',)
    search_fields = ('suspension',)

@admin.register(WheelSizeModel)
class WheelSizeAdmin(admin.ModelAdmin):
    list_display = ('wheel_size', 'created')
    list_filter = ('created',)
    search_fields = ('wheel_size',)

@admin.register(RearSuspensionTravelModel)
class RearSuspensionTravelAdmin(admin.ModelAdmin):
    list_display = ('rear_suspension_travel', 'created')
    list_filter = ('created',)
    search_fields = ('rear_suspension_travel',)

@admin.register(BikeCategoryModel)
class BikeCategoryAdmin(PreserveFilesAdminMixin, admin.ModelAdmin):
    list_display = ('category_name', 'preview_image', 'created')
    list_filter = ('created',)
    search_fields = ('category_name',)
    readonly_fields = ('preview_image',)
    
    def preview_image(self, obj):
        if obj.category_image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.category_image.url)
        return "-"
    preview_image.short_description = "Preview"

@admin.register(BikeBrandModel)
class BikeBrandAdmin(PreserveFilesAdminMixin, admin.ModelAdmin):
    list_display = ('brand_name', 'preview_image','online_purchase_enabled', 'created')
    list_filter = ('created','online_purchase_enabled')
    search_fields = ('brand_name', 'brand_description')
    readonly_fields = ('preview_image',)
    
    def preview_image(self, obj):
        if obj.brand_image:
            return format_html('<img src="{}" width="100" height="25" style="object-fit: cover;" />', obj.brand_image.url)
        return "-"
    preview_image.short_description = "Preview"

@admin.register(ColorModel)
class ColorAdmin(PreserveFilesAdminMixin, admin.ModelAdmin):
    list_display = ('color_name', 'color_code', 'color_code_2', 'preview_color', 'created')
    list_filter = ('created',)
    search_fields = ('color_name', 'color_code')
    readonly_fields = ('preview_color',)
    
    def preview_color(self, obj):
        if obj.color_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 4px;" />',
                obj.color_image.url
            )
        
        # Check if color_code_2 exists and has a value
        if obj.color_code_2:
            return format_html(
                '<div style="width: 50px; height: 50px; background: linear-gradient(135deg, {} 50%, {} 50%); border-radius: 4px; border: 1px solid #ddd;"></div>',
                obj.color_code,
                obj.color_code_2
            )
        
        return format_html(
            '<div style="width: 50px; height: 50px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;"></div>',
            obj.color_code
        )
    
    preview_color.short_description = "Preview"


@admin.register(SizeModel)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('size', 'created')
    search_fields = ('size',)

@admin.register(SpecialTagModel)
class SpecialTagAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'created')
    search_fields = ('tag_name',)

    verbose_name = "Special Tag"
    verbose_name_plural = "Special Tags"

class BikeSizesModelNestedInline(nested_admin.NestedTabularInline):
    model = BikeSizesModel
    extra = 1
    fk_name = 'bike'
    fields = (
        'bike_size',
        'price',
        'stock',
        'is_available',
        'is_out_of_stock',
        'is_discount',
        'discount_price',
        'discount_percentage',
    )

@admin.register(BikeSizesModel)
class BikeSizesAdmin(admin.ModelAdmin):
    list_display = ('bike', 'bike_size', 'price', 'is_discount', 'discount_price', 'discount_percentage', 'stock', 'is_available', 'is_out_of_stock')
    list_filter = ('bike__brand', 'bike_size', 'is_discount', 'is_available', 'is_out_of_stock')
    search_fields = ('bike__name', 'bike_size__size')

class BikeImagesModelNestedInline(PreserveFilesAdminMixin, nested_admin.NestedTabularInline):
    model = BikeImagesModel
    extra = 1
    fk_name = 'color'
    
class BikeColorsModelNestedInline(nested_admin.NestedTabularInline):
    model = BikeColorsModel
    extra = 1
    fk_name = 'bike'
    inlines = [BikeImagesModelNestedInline]

class BikeSpecValueModelInline(nested_admin.NestedTabularInline):
    model = BikeSpecValueModel
    extra = 1
    fk_name = 'bike_spec_label'

class BikeSpecLabelModelInline(nested_admin.NestedTabularInline):
    model = BikeSpecLabelModel
    extra = 1
    inlines = [BikeSpecValueModelInline]
    
class BikePostersModelInline(PreserveFilesAdminMixin, nested_admin.NestedStackedInline):
    model = BikePostersModel
    extra = 1

class BikeDownloadsModelInline(PreserveFilesAdminMixin, nested_admin.NestedStackedInline):
    model = BikeDownloadsModel
    extra = 1

@admin.register(BikeModel)
class BikeAdmin(PreserveFilesAdminMixin, nested_admin.NestedModelAdmin):
    list_display = ('brand_img','name', 'special_tag', 'brand', 'category', 'price', 'discount_price', 'discount_percentage')
    search_fields = ('name', 'brand__brand_name', 'category__category_name', 'price', 'discount_price', 'discount_percentage')
    list_filter = ('special_tag', 'brand', 'category', 'is_discount', 'is_available', 'is_out_of_stock', 'online_purchase_enabled')

    save_as = True
    actions = ['duplicate_bike']

    inlines = [
        BikeSizesModelNestedInline,
        BikeColorsModelNestedInline,
        BikeSpecLabelModelInline,
        BikePostersModelInline,
        BikeDownloadsModelInline
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'brand',
                'category',
                'special_tag',
                'description',
            )
        }),
        ('Specifications', {
            'fields': (
                'wheel_size',
                'material',
                'suspension',
                'rear_suspension_travel',
                'sizes',
            )
        }),
        ('Default / Base Pricing & Stock', {
            'description': 'Base price for the bike. When size variants are added below in "Bike Sizes & Prices", each size has its own specific price and stock.',
            'fields': (
                'price',
                'stock',
                'is_available',
                'is_out_of_stock',
                'is_discount',
                'discount_price',
                'discount_percentage',
            )
        }),
        ('Display & Media', {
            'fields': (
                'background_color',
                'text_color',
                'is_dark',
                'is_featured',
                'featured_image',
                'youtube_link',
            )
        }),
        ('E-commerce & Shipping', {
            'fields': (
                'online_purchase_enabled',
                'shipping_charge',
            )
        }),
    )
    
    def brand_img(self, obj):
        if obj.brand.brand_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.brand.brand_image.url)
        return "-"
    brand_img.short_description = "Brand"

    @admin.action(description="Duplicate selected bikes (creates a full copy with all inlines)")
    def duplicate_bike(self, request, queryset):
        duplicated = []
        for bike in queryset:
            cloned = clone_bike(bike)
            duplicated.append(cloned)

        if len(duplicated) == 1:
            cloned = duplicated[0]
            self.message_user(
                request,
                format_html(
                    'Bike duplicated successfully as <strong>"{}"</strong>. You are now editing the duplicate. Update the name and any other fields, then click Save.',
                    cloned.name
                ),
                level=messages.SUCCESS
            )
            return HttpResponseRedirect(reverse('admin:Application_bikemodel_change', args=[cloned.pk]))
        else:
            self.message_user(
                request,
                f"Successfully duplicated {len(duplicated)} bike(s). You can now edit each duplicate to change its name and details.",
                level=messages.SUCCESS
            )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/duplicate/',
                self.admin_site.admin_view(self.duplicate_bike_view),
                name='Application_bikemodel_duplicate',
            ),
        ]
        return custom_urls + urls

    def duplicate_bike_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj is None:
            self.message_user(request, "Bike not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:Application_bikemodel_changelist'))

        if not self.has_add_permission(request):
            self.message_user(request, "You do not have permission to duplicate bikes.", level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:Application_bikemodel_change', args=[object_id]))

        cloned = clone_bike(obj)
        self.message_user(
            request,
            format_html(
                'Bike duplicated successfully as <strong>"{}"</strong>. You are now editing the duplicate. Update the name and any other fields, then click Save.',
                cloned.name
            ),
            level=messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('admin:Application_bikemodel_change', args=[cloned.pk]))

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            try:
                extra_context['duplicate_url'] = reverse('admin:Application_bikemodel_duplicate', args=[object_id])
            except Exception:
                pass
        return super().changeform_view(request, object_id=object_id, form_url=form_url, extra_context=extra_context)

class AccessoriesSubCategoryInline(admin.TabularInline):
    model = AccessoriesSubCategoryModel
    extra = 1

@admin.register(AccessoriesCategoryModel)
class AccessoriesCategoryAdmin(PreserveFilesAdminMixin, admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
    inlines = [AccessoriesSubCategoryInline]

class AccessoryImagesInline(PreserveFilesAdminMixin, admin.TabularInline):
    model = AccessoryImagesModel
    extra = 1

@admin.register(AccessoriesModel)
class AccessoriesAdmin(PreserveFilesAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name','brand')
    list_filter = ('name','brand')
    inlines = [AccessoryImagesInline]

    save_as = True
    actions = ['duplicate_accessory']

    @admin.action(description="Duplicate selected accessories (creates a copy with all images)")
    def duplicate_accessory(self, request, queryset):
        duplicated = []
        for acc in queryset:
            cloned = clone_accessory(acc)
            duplicated.append(cloned)

        if len(duplicated) == 1:
            cloned = duplicated[0]
            self.message_user(
                request,
                format_html(
                    'Accessory duplicated successfully as <strong>"{}"</strong>. You are now editing the duplicate. Update the name and any other fields, then click Save.',
                    cloned.name
                ),
                level=messages.SUCCESS
            )
            return HttpResponseRedirect(reverse('admin:Application_accessoriesmodel_change', args=[cloned.pk]))
        else:
            self.message_user(
                request,
                f"Successfully duplicated {len(duplicated)} accessory(ies). You can now edit each duplicate to change its name and details.",
                level=messages.SUCCESS
            )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/duplicate/',
                self.admin_site.admin_view(self.duplicate_accessory_view),
                name='Application_accessoriesmodel_duplicate',
            ),
        ]
        return custom_urls + urls

    def duplicate_accessory_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj is None:
            self.message_user(request, "Accessory not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:Application_accessoriesmodel_changelist'))

        if not self.has_add_permission(request):
            self.message_user(request, "You do not have permission to duplicate accessories.", level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:Application_accessoriesmodel_change', args=[object_id]))

        cloned = clone_accessory(obj)
        self.message_user(
            request,
            format_html(
                'Accessory duplicated successfully as <strong>"{}"</strong>. You are now editing the duplicate. Update the name and any other fields, then click Save.',
                cloned.name
            ),
            level=messages.SUCCESS
        )
        return HttpResponseRedirect(reverse('admin:Application_accessoriesmodel_change', args=[cloned.pk]))

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            try:
                extra_context['duplicate_url'] = reverse('admin:Application_accessoriesmodel_duplicate', args=[object_id])
            except Exception:
                pass
        return super().changeform_view(request, object_id=object_id, form_url=form_url, extra_context=extra_context)

@admin.register(GuideAndTrainerModel)
class GuideAndTrainerAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)
    list_filter = ('created',)

@admin.register(ShippingChargeModel)
class ShippingChargeAdmin(admin.ModelAdmin):
    list_display = ('name', 'charge', 'created')
    search_fields = ('name',)
    list_filter = ('created','name')