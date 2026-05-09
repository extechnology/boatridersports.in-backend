from django.urls import path, include
from .order_views import *

urlpatterns = [
    path('total-orders/',TotalOrdersAPIView.as_view(),name = 'total-orders'),
    path('order-status-update/', OrderStatusUpdate.as_view(), name='order-status-update'),
]