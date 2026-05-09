from django.urls import path
from .product_views import *


urlpatterns = [
    path('bikes/', BikesAPIView.as_view(), name='bikes'),
    path('products-filter-side-bar/', ProductsFilterSideBarAPIView.as_view(), name='products-filter-side-bar'),
    path('products-filtered/', ProductFilterView.as_view(), name='product-filter-view'),
    path('product-detail-page/<str:product_type>/<str:product_id>/', ProductDetailPage.as_view(), name='product-detail-page'),
    path('suggested-product/', SuggestedProduct.as_view(), name='suggested-product'),
    path('navbar-items/', NavbarItemsAPIView.as_view(), name='navbar-items'),
    path('shop-buy/', ShopBuy.as_view(), name='shop-buy'),
    path('featured-product/', FeaturdProduct.as_view(), name='featured-product'),
    path('brands-images/', BrandsImages.as_view(), name='brands-images'),
    
]