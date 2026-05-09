from django.urls import path
from .product_views import *

urlpatterns = [
    path('bikes/', BikeListView.as_view(), name='bike-list'),
    path('accessories/', AccessoryListView.as_view(), name='accessory-list'),

]