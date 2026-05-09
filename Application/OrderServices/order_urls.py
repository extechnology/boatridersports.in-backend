from Application.OrderServices.order_views import VerifyOrderPayment
from django.urls import path
from .order_views import *

urlpatterns = [
    path('user-orders/', UserOrders.as_view(), name = 'user-orders'),
    path('create-order/',InitaiteChcekOutAPIview.as_view(), name = 'user-order-create'),
    path('verify-order/',VerifyOrderPayment.as_view(), name = 'user-order-verify')
]