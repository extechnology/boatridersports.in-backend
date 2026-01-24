from rest_framework import serializers
from .ui_models import *

class HomeSliderVideoSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    class Meta:
        model = HomeSliderVideoModel
        fields = [
            'desktop_video',
            'mobile_video',
            'title',
            'sub_title',
            'description',
            'created_at',
            'updated_at',
        ]
