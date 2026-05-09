from django.urls import path
from .brand_views import *

urlpatterns = [
    path('list/', BrandListView.as_view(), name='brand_list'),
]