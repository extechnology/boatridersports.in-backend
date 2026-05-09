from rest_framework import serializers
from Application.ProductServices.product_models import BikeBrandModel

class BrandSerializerDashboard(serializers.ModelSerializer):
    class Meta:
        model = BikeBrandModel
        fields = [
            'brand_name',
            'brand_image',
            'brand_description',
        ]