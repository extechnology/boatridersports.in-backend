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
from Application.ProfileServices.profile_models import UserAddress
from Application.AuthenticationServices.auth_models import User


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorModel
        fields = '__all__'


class BikeBrandSerializers(serializers.ModelSerializer):
    class Meta:
        model = BikeBrandModel
        fields = ['brand_name']

    def to_representation(self, obj):
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


class UserAddressSerializerDashboard(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = UserAddress
        fields = [
            'id',
            'unique_id',
            'name',
            'phone_number',
            'address_type',
            'address',
            'city',
            'state',
            'pincode',
            'is_default',
            'full_address',
            'created',
            'updated'
        ]

    def get_full_address(self, obj):
        if not obj:
            return ""
        parts = [p for p in [obj.address, obj.city, obj.state] if p]
        addr = ", ".join(parts)
        if obj.pincode:
            addr = f"{addr} - {obj.pincode}" if addr else obj.pincode
        return addr


class UserDetailsSerializerDashboard(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'unique_id', 'username', 'email', 'phone', 'fullname']


class UserOrdersModelSerializerDashboard(serializers.ModelSerializer):
    user_address = UserAddressSerializerDashboard(read_only=True)
    user_address_id = serializers.IntegerField(source='user_address.id', read_only=True)
    user_details = UserDetailsSerializerDashboard(source='user', read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    all_products = serializers.SerializerMethodField()

    class Meta:
        model = UserOrdersModel
        fields = '__all__'

    def get_customer_name(self, obj):
        if obj.user_address and obj.user_address.name:
            return obj.user_address.name
        if obj.user:
            return obj.user.fullname or obj.user.username or ""
        return ""

    def get_customer_email(self, obj):
        return obj.user.email if obj.user and obj.user.email else ""

    def get_customer_phone(self, obj):
        if obj.user_address and obj.user_address.phone_number:
            return obj.user_address.phone_number
        if obj.user and getattr(obj.user, 'phone', None):
            return obj.user.phone
        return ""

    def get_full_address(self, obj):
        if not obj.user_address:
            return ""
        addr = obj.user_address
        parts = [p for p in [addr.address, addr.city, addr.state] if p]
        addr_str = ", ".join(parts)
        if addr.pincode:
            addr_str = f"{addr_str} - {addr.pincode}" if addr_str else addr.pincode
        return addr_str

    def get_all_products(self, obj):
        bike_orders = BikeOrderItemsSerializerDashboard(obj.bike_orders.all(), many=True, context=self.context).data
        accessories_orders = AccessoriesOrderItemsSerializerDashboard(obj.accessories_orders.all(), many=True, context=self.context).data
        return bike_orders + accessories_orders


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOrdersModel
        fields = '__all__'
