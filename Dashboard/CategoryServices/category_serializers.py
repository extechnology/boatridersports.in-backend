from Application.ProductServices.product_models import BikeCategoryModel
from rest_framework import serializers

class CategorySerializerDashboard(serializers.ModelSerializer):
    class Meta:
        model = BikeCategoryModel
        fields = [
            'category_name',
            'category_image',
            'created',
        ]