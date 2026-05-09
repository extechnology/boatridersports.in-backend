from rest_framework import serializers

from Application.OrderServices.order_models import (
    UserOrdersModel,
    AccessoriesOrderItems,
    BikeOrderItems
)

from Application.ProductServices.product_models import (
    BikeModel,
    AccessoriesModel,
    BikeColorsModel,
    SizeModel,
    BikeImagesModel,
    BikeBrandModel,
    ColorModel,
    AccessoryImagesModel
)

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorModel
        fields = '__all__'

class BikeBrandSerializers(serializers.ModelSerializer):
    class Meta:
        model = BikeBrandModel
        fields = ['brand_name']

    def to_representation(self,obj):
        return obj.brand_name

class BikeImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeImagesModel
        fields = '__all__'

    def to_representation(self, obj):
        return obj.image.url if obj.image else None


class BikeColorsSerializer(serializers.ModelSerializer):
    bike_images = BikeImagesSerializer(many=True)
    color = ColorSerializer()
    class Meta:
        model = BikeColorsModel
        fields = '__all__'

class SizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeModel
        fields = '__all__'

class BikeModelSerializer(serializers.ModelSerializer):
    brand = BikeBrandSerializers()
    category_name = serializers.CharField(source='category.category_name', read_only=True)

    class Meta:
        model = BikeModel
        fields = ['unique_id', 'name', 'price', 'product_type', 'brand', 'category_name']


class AccessoriesModelSerializer(serializers.ModelSerializer):
    brand = BikeBrandSerializers()
    category_name = serializers.CharField(source='sub_category.category.name', read_only=True)

    class Meta:
        model = AccessoriesModel
        fields = ['unique_id', 'name', 'price', 'product_type', 'brand', 'category_name']


class AccessoriesOrderItemsSerializerDashboard(serializers.ModelSerializer):
    accessory = AccessoriesModelSerializer(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = AccessoriesOrderItems
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.accessory:
            first_image = obj.accessory.accessory_images.first()
            if first_image and first_image.image:
                return request.build_absolute_uri(first_image.image.url) if request else first_image.image.url
        return None

class BikeOrderItemsSerializerDashboard(serializers.ModelSerializer):
    bike = BikeModelSerializer(read_only=True)
    color = serializers.CharField(source='color.color.color_name', read_only=True)
    size = serializers.CharField(source='size.size', read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = BikeOrderItems
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.color:
            first_image = obj.color.bike_images.first()
            if first_image and first_image.image:
                return request.build_absolute_uri(first_image.image.url) if request else first_image.image.url
        return None


class UserOrdersModelSerializerDashboard(serializers.ModelSerializer):
    all_products = serializers.SerializerMethodField()
    user = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = UserOrdersModel
        fields = '__all__'
    
    def get_all_products(self, obj):
        bike_orders = BikeOrderItemsSerializerDashboard(obj.bike_orders.all(), many=True, context=self.context).data
        accessories_orders = AccessoriesOrderItemsSerializerDashboard(obj.accessories_orders.all(), many=True, context=self.context).data
        return bike_orders + accessories_orders

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOrdersModel
        fields = '__all__'