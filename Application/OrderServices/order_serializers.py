from rest_framework import serializers

# Import models
from .order_models import *
from Application.ProductServices.product_models import (
    BikeModel,
    AccessoriesModel,
    BikeColorsModel,
    SizeModel
    )
from Application.ProfileServices.profile_models import UserAddress
from Application.CartServices.usercart_serializers import (
    BikesSerializer, 
    AccessoriesSerializer, 
    BikeColorsSerializer, 
    SizesSerializer
)

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'


class AccessoriesOrdeItemsSerializer(serializers.ModelSerializer):
    accessory = AccessoriesSerializer(read_only=True)

    class Meta:
        model = AccessoriesOrderItems
        fields = '__all__'

        
class BikeOrdeItemsSerializer(serializers.ModelSerializer):
    bike = BikesSerializer(read_only=True)
    color = BikeColorsSerializer(read_only=True)
    size = SizesSerializer(read_only=True)
    
    class Meta:
        model = BikeOrderItems
        fields = '__all__'

class UserOrdersSerializer(serializers.ModelSerializer):
    user_address = UserAddressSerializer(read_only=True)
    all_products = serializers.SerializerMethodField()

    class Meta:
        model = UserOrdersModel
        fields = '__all__'

    def get_all_products(self, obj):
        bike_orders = BikeOrdeItemsSerializer(obj.bike_orders.all(), many=True, context=self.context).data
        accessories_orders = AccessoriesOrdeItemsSerializer(obj.accessories_orders.all(), many=True, context=self.context).data
        return bike_orders + accessories_orders