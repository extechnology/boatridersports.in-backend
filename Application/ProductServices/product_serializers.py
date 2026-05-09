from rest_framework import serializers
from .product_models import (
    BikeCategoryModel, BikeBrandModel, ColorModel, SizeModel, SpecialTagModel,
    BikeModel, BikeSizesModel, BikeColorsModel, BikeImagesModel,
    BikeSpecLabelModel, BikeSpecValueModel, BikePostersModel, BikeDownloadsModel,
    MaterialModel, SuspensionModel, WheelSizeModel, RearSuspensionTravelModel,
    AccessoriesCategoryModel, GuideAndTrainerModel, AccessoriesSubCategoryModel, 
    AccessoriesModel, BikeReviewsModel, AccessoryImagesModel

)


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialModel
        fields = ['material']


class SuspensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuspensionModel
        fields = ['suspension']


class WheelSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WheelSizeModel
        fields = ['wheel_size']


class RearSuspensionTravelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RearSuspensionTravelModel
        fields = ['rear_suspension_travel']


class BikeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeCategoryModel
        fields = ['category_name', 'category_image']


class BikeBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeBrandModel
        fields = ['brand_name', 'brand_image', 'brand_description','online_purchase_enabled']


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorModel
        fields = [
            'color_name',
            'color_code',
            'color_code_2',
            'color_image'
        ]


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeModel
        fields = ['size']
    
    def to_representation(self, instance):
        return instance.size


class SpecialTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialTagModel
        fields = ['tag_name']



class BikeSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeSizesModel
        fields = ['bike_size']  # This will output the string representation
    
    def to_representation(self, instance):
        # Return just the size string
        return instance.bike_size.size

# --------------------
# BIKE IMAGE SERIALIZER
# --------------------

class BikeImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeImagesModel
        fields = ['image']
    
    def to_representation(self, instance):
        # Return just the image URL
        request = self.context.get('request')
        if request:
            return f"{request.scheme}://{request.get_host()}{instance.image.url}"
        return instance.image.url

    

# --------------------
# BIKE COLOR SERIALIZER
# --------------------

class BikeColorSerializer(serializers.ModelSerializer):
    color = serializers.CharField(source='color.color_name')
    bike_images = BikeImagesSerializer(many=True, read_only=True,)
    color_code = serializers.SerializerMethodField()
    class Meta:
        model = BikeColorsModel
        fields = [
            'color',
            'bike_images',
            'color_code'
        ]
    
    def get_color_code(self, obj):
        color_1 = obj.color.color_code
        color_2 = obj.color.color_code_2
        colors = []

        if color_1 and color_2 != None:
            colors = [color_1, color_2]
        elif color_1 != None:
            colors = [color_1]
        else:
            colors = []

        return colors


# --------------------
# BIKE SPEC SERIALIZERS
# --------------------

class BikeSpecValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeSpecValueModel
        fields = ['name', 'value']


class BikeSpecLabelSerializer(serializers.ModelSerializer):
    bike_spec_values = BikeSpecValueSerializer(  # Changed from bike_spec_label
        many=True, read_only=True
    )
    
    class Meta:
        model = BikeSpecLabelModel
        fields = [
            'label', 
            'bike_spec_values'  # Changed from bike_spec_label
        ]
# --------------------
# POSTERS & DOWNLOADS
# --------------------

class BikePosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikePostersModel
        fields = ['poster', 'title', 'description']


class BikeDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeDownloadsModel
        fields = ['file', 'title']


# --------------------
# MAIN BIKE SERIALIZER
# --------------------


class BikeSerializer(serializers.ModelSerializer):
    special_tag = serializers.CharField(source='special_tag.tag_name')
    brand = serializers.CharField(source='brand.brand_name')
    category = serializers.CharField(source='category.category_name')

    wheel_size = serializers.StringRelatedField(many=True)
    material = serializers.StringRelatedField(many=True)
    suspension = serializers.StringRelatedField(many=True)

    bike_posters = BikePosterSerializer(many=True, read_only=True)
    bike_downloads = BikeDownloadSerializer(many=True, read_only=True)

    sizes = SizeSerializer(
        many=True,
    )

    bike_colors = BikeColorSerializer(many=True, read_only=True)

    bike_spec_labels = BikeSpecLabelSerializer(
        many=True,
        
        read_only=True
    )
    rear_suspension_travel = serializers.StringRelatedField(many=True)
    
    youtube_video_id = serializers.SerializerMethodField()

    class Meta:
        model = BikeModel
        fields = [
            'product_type',
            'id',
            'unique_id',
            'name',
            'description',

            'wheel_size',
            'material',
            'suspension',
            'rear_suspension_travel',

            'special_tag',
            'brand',
            'category',


            'price',
            'stock',
            'is_available',
            'is_out_of_stock',
            'is_discount',
            'discount_price',
            'discount_percentage',

            'background_color',
            'text_color',
            'is_dark',

            'is_featured',
            'featured_image',
            'youtube_link',
            'youtube_video_id',  # Add this field

            'sizes',
            'bike_colors',
            'bike_spec_labels',
            'bike_posters',
            'bike_downloads',
            'online_purchase_enabled',
            'shipping_charge',

            'created'
        ]

    def get_youtube_video_id(self, obj):
        youtube_link = obj.youtube_link
        
        if not youtube_link:
            return None
        
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})',
            r'youtube\.com\/watch\?\S*v=([\w-]{11})',
            r'youtube\.com\/embed\/([\w-]{11})',
            r'youtube\.com\/v\/([\w-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_link)
            if match:
                return match.group(1)
        
        return None


class AccessoriesCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessoriesCategoryModel
        fields = ['name']


class AccessoriesSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessoriesSubCategoryModel
        fields = ['name']
    
    def to_representation(self, instance):
        return instance.name
    

class AccessoryImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessoryImagesModel
        fields = ['image']
    
    def to_representation(self, instance):
        request = self.context.get('request')
        if request:
            return f"{request.scheme}://{request.get_host()}{instance.image.url}"
        return instance.image.url


class AccessoriesSerializer(serializers.ModelSerializer):
    sub_category = serializers.CharField(source='sub_category.category.name', read_only=True)
    accessory_images = AccessoryImagesSerializer(many=True, read_only=True)
    special_tag = serializers.CharField(source='special_tag.tag_name', read_only=True)
    brand = serializers.CharField(source='brand.brand_name', read_only=True)
    category = serializers.CharField(source='sub_category.category.name', read_only=True)  

    class Meta:
        model = AccessoriesModel
        fields = [
            'product_type',
            'id',
            'unique_id',
            'name',
            'category',
            'description',

            'special_tag',
            'brand',
            'price',
            'stock',
            'is_available',
            'is_out_of_stock',
            'is_discount',
            'discount_price',
            'discount_percentage', 
            'sub_category', 
            'accessory_images',
            'is_dark',
            'online_purchase_enabled',
            'shipping_charge',
            'created'
        ]


class BikeBrandImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeBrandModel
        fields = ['brand_image']
    
    def to_representation(self, instance):
        request = self.context.get('request')
        if request:
            return f"{request.scheme}://{request.get_host()}{instance.brand_image.url}"
        return instance.brand_image.url