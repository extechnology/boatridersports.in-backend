from rest_framework import serializers
from django.db.models import Sum

from Application.AuthenticationServices.auth_models import User
from Application.OrderServices.order_models import UserOrdersModel




class UserSerializerDashboard(serializers.ModelSerializer):
    total_orders = serializers.SerializerMethodField()
    total_amount_spend = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            'unique_id',
            'username',
            'email',
            'phone',
            'total_orders',
            'total_amount_spend',
            'date_joined',
        ]

    def get_total_orders(self,obj):
        return UserOrdersModel.objects.filter(user=obj).count()
    
    def get_total_amount_spend(self,obj):
        return UserOrdersModel.objects.filter(user=obj).aggregate(total_amount=Sum('total_amount'))['total_amount']



