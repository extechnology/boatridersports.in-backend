from rest_framework import serializers

from Application.OrderServices.order_models import (
    UserOrdersModel,
    BikeOrderItems,
    AccessoriesOrderItems
)

from Application.ProductServices.product_models import (
    BikeModel,
    AccessoriesModel
)


class UserOrdersSerializerDashboard(serializers.ModelSerializer):
    class Meta:
        model = UserOrdersModel
        fields = '__all__'


