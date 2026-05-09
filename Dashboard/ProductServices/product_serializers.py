from rest_framework import serializers
from Application.ProductServices.product_models import (
    BikeCategoryModel, BikeBrandModel, BikeModel, BikeColorsModel, BikeImagesModel,
    MaterialModel, SuspensionModel, WheelSizeModel,
    AccessoriesCategoryModel, AccessoriesSubCategoryModel, AccessoriesModel,AccessoryImagesModel

)

class BikeBrandSerializers(serializers.ModelSerializer):
    class Meta:
        model = BikeBrandModel
        fields = [
            'brand_name',
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['brand_name'] = instance.brand_name
        return representation

class BikeCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = BikeCategoryModel
        fields = [
            'category_name',
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['category_name'] = instance.category_name
        return representation
    

class BikeMaterialSerializers(serializers.ModelSerializer):
    class Meta:
        model = MaterialModel
        fields = [
            'material',
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['material'] = instance.material
        return representation


class BikeSuspensionSerializers(serializers.ModelSerializer):
    class Meta:
        model = SuspensionModel
        fields = [
            'suspension',
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['suspension'] = instance.suspension
        return representation


class BikeWheelSizeSerializers(serializers.ModelSerializer):
    class Meta:
        model = WheelSizeModel
        fields = [
            'wheel_size',
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['wheel_size'] = instance.wheel_size
        return representation

class BikeSerializer(serializers.ModelSerializer):
    brand = serializers.SlugRelatedField(slug_field='brand_name', read_only=True)
    category = serializers.SlugRelatedField(slug_field='category_name', read_only=True)
    material = serializers.SlugRelatedField(slug_field='material', many=True, read_only=True)
    suspension = serializers.SlugRelatedField(slug_field='suspension', many=True, read_only=True)
    wheel_size = serializers.SlugRelatedField(slug_field='wheel_size', many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    
    class Meta:
        model = BikeModel
        fields = [
            'name',
            'description',
            'price',
            'stock',
            'brand',
            'category',
            'material',
            'suspension',
            'wheel_size',
            'image_url',
            
        ]
    
    def get_image_url(self, instance):
        color = BikeColorsModel.objects.filter(bike=instance).first()
        if color:
            image = BikeImagesModel.objects.filter(color=color).first()
            if image and image.image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(image.image.url)
                return image.image.url
        return None
    

class AccessoryCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = AccessoriesCategoryModel
        fields = [
            'name',
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['name'] = instance.name
        return representation

class AccessorySubCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = AccessoriesSubCategoryModel
        fields = [
            'name',
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['name'] = instance.name
        return representation

class AccessorySerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='name', read_only=True)
    sub_category = serializers.SlugRelatedField(slug_field='name', read_only=True)
    image_url = serializers.SerializerMethodField()
    brand = serializers.SlugRelatedField(slug_field='brand_name', read_only=True)
    
    class Meta:
        model = AccessoriesModel
        fields = [
            'name',
            'description',
            'price',
            'stock',
            'category',
            'sub_category',
            'image_url',
            'brand',
        ]
    
    def get_image_url(self, instance):
       image = AccessoryImagesModel.objects.filter(accessory=instance).first()
       if image and image.image:
           request = self.context.get('request')
           if request:
               return request.build_absolute_uri(image.image.url)
           return image.image.url
       return None
