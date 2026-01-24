from django.urls import path
from .product_views import *


urlpatterns = [
    path('bikes/', BikesAPIView.as_view(), name='bikes'),
    path('bikes-filtered/', BikesFilteredAPIView.as_view(), name='bikes-filtered'),
    path('products-filter-side-bar/', ProductsFilterSideBarAPIView.as_view(), name='products-filter-side-bar'),
    path('products-filtered/', CustomProductFilterView.as_view(), name='custome-product-filterview'),
    path('product-detail-page/<str:product_type>/<str:product_id>/', ProductDetailPage.as_view(), name='product-detail-page'),
    path('suggested-product/', SuggestedProduct.as_view(), name='suggested-product'),
]