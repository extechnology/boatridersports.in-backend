from rest_framework import serializers
from .ui_models import *

class HomeSliderVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeSliderVideoModel
        fields = '__all__'