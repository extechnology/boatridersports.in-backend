from rest_framework import serializers
from Application.CartServices.usercart_models import(
    UserCartModel,
    UserCartItemsModelBike,
    UserCartItemsModelAccessories
    )
from Application.ProductServices.product_models import(
    BikeModel,
    AccessoriesModel,
    BikeColorsModel,
    BikeSizesModel,
    SizeModel,
    BikeImagesModel,
    AccessoryImagesModel,
    ColorModel,
    BikeBrandModel,
    BikeCategoryModel
    )


class BikeBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeBrandModel
        fields = '__all__'
    
    def to_representation(self, instance):
        return instance.brand_name

class BikeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeCategoryModel
        fields = '__all__'
    
    def to_representation(self, instance):
        return instance.category_name


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorModel
        fields = ['color_name']

    def to_representation(self, instance):
        return instance.color_name

class BikeColorsSerializerProduct(serializers.ModelSerializer):
    brand = BikeBrandSerializer(read_only=True)
    category = BikeCategorySerializer(read_only=True)
    class Meta:
        model = BikeColorsModel
        fields = '__all__'
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['color'] = instance.color.color_name if instance.color else None
        response['bike_images'] = BikeImagesSerializer(instance.bike_images.all(), many=True, context=self.context).data
        return response


class BikesSerializer(serializers.ModelSerializer):
    bike_colors = BikeColorsSerializerProduct(many=True, read_only=True)
    class Meta:
        model = BikeModel
        fields = '__all__'

class AccessoryImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccessoryImagesModel
        fields = ['image']

    def to_representation(self, instance):
        request = self.context.get('request')
        if instance.image:
            if request:
                return request.build_absolute_uri(instance.image.url)
            return instance.image.url
        return None

class AccessoriesSerializer(serializers.ModelSerializer):
    accessory_images = AccessoryImagesSerializer(many=True, read_only=True)
    class Meta:
        model = AccessoriesModel
        fields = '__all__'

class BikeImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeImagesModel
        fields = ['image']

    def to_representation(self, instance):
        request = self.context.get('request')
        if instance.image:
            if request:
                return request.build_absolute_uri(instance.image.url)
            return instance.image.url
        return None

class BikeColorsSerializer(serializers.ModelSerializer):
    bike_images = BikeImagesSerializer(many=True, read_only=True)
    color = ColorSerializer()
    class Meta:
        model = BikeColorsModel
        fields = '__all__'

class SizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeModel
        fields = '__all__'

class UserCartItemsModelBikeSerializer(serializers.ModelSerializer):
    bike = BikesSerializer(read_only=True)
    size = SizesSerializer(read_only=True)
    color = BikeColorsSerializer(read_only=True)
    class Meta:
        model = UserCartItemsModelBike
        fields = '__all__'

class UserCartItemsModelAccessoriesSerializer(serializers.ModelSerializer):
    accessory = AccessoriesSerializer(read_only=True)
    class Meta:
        model = UserCartItemsModelAccessories
        fields = '__all__'

class UserCartModelSerializer(serializers.ModelSerializer):
    total_products = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    orginal_amount = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()
    total_bikes = serializers.SerializerMethodField()
    total_accessories = serializers.SerializerMethodField()
    all_products = serializers.SerializerMethodField()
    shipping_charge = serializers.SerializerMethodField()

    class Meta:
        model = UserCartModel
        fields = '__all__'

    def get_total_products(self, obj):
        return obj.user_cart_bike_items.count() + obj.user_cart_accessory_items.count()
    
    def get_total_amount(self, obj):
        total_bike_amount = 0
        total_accessory_amount = 0
        for item in obj.user_cart_bike_items.all():
            if item.bike.is_discount:
                total_bike_amount += item.bike.discount_price * item.quantity
            else:
                total_bike_amount += item.bike.price * item.quantity
        for item in obj.user_cart_accessory_items.all():
            if item.accessory.is_discount:
                total_accessory_amount += item.accessory.discount_price * item.quantity
            else:
                total_accessory_amount += item.accessory.price * item.quantity
        return total_bike_amount + total_accessory_amount

    def get_orginal_amount(self, obj):
        total_bike_amount = 0
        total_accessory_amount = 0
        for item in obj.user_cart_bike_items.all():
            total_bike_amount += item.bike.price * item.quantity
        for item in obj.user_cart_accessory_items.all():
            total_accessory_amount += item.accessory.price * item.quantity
        return total_bike_amount + total_accessory_amount   

    def get_total_discount(self, obj):
        return self.get_orginal_amount(obj) - self.get_total_amount(obj)
    
    def get_total_bikes(self, obj):
        return obj.user_cart_bike_items.count()
    
    def get_shipping_charge(self, obj):
        total_amount = self.get_total_amount(obj)
        shipping = 0
        has_bike = obj.user_cart_bike_items.exists()
        
        if has_bike:
            if total_amount > 10000:
                return 0
            # If there's a bike, ONLY apply bike shipping charges
            for item in obj.user_cart_bike_items.all():
                shipping += item.bike.shipping_charge * item.quantity
        else:
            # Cart only contains accessories
            if total_amount > 1000:
                return 0
            # Apply accessory shipping charges for carts <= 1000 rs
            for item in obj.user_cart_accessory_items.all():
                shipping += item.accessory.shipping_charge * item.quantity
                    
        return shipping
    
    def get_total_accessories(self, obj):
        return obj.user_cart_accessory_items.count()

    def get_all_products(self, obj):
        bike_items = UserCartItemsModelBikeSerializer(obj.user_cart_bike_items.all(), many=True, context=self.context).data
        accessory_items = UserCartItemsModelAccessoriesSerializer(obj.user_cart_accessory_items.all(), many=True, context=self.context).data
        return bike_items + accessory_items