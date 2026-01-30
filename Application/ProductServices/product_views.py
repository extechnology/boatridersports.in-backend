from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from itertools import chain

from .product_serializers import *
from .product_models import *
from .product_tasks import build_bike_sidebar,build_accessory_sidebar

from .product_filters import bike_filters,accessories_filters
from django.db.models import Prefetch,Subquery

from django_filters.rest_framework import DjangoFilterBackend
from .product_filters import (
    BikeFilter,
    AccessoriesFilter
)

import hashlib
import json


class CustomPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

class BikesAPIView(APIView):
    def get(self, request):
        bikes = BikeModel.objects.all()
        serializer = BikeSerializer(bikes, many=True,context={'request': request})
        return Response(serializer.data)


class ProductsFilterSideBarAPIView(APIView):
    def get(self, request):
        sidebar = request.query_params.get("sidebar")
        
        if sidebar == "bike":

            data = cache.get("sidebar_bike")
            if not data:
                # Call synchronously for immediate response
                data = build_bike_sidebar()
                # Optionally trigger async refresh in background
                build_bike_sidebar.delay()
            return Response(data)
            
        elif sidebar == "accessories":
            data = cache.get("sidebar_accessory")
            if not data:
                # Call synchronously for immediate response
                data = build_accessory_sidebar()
                # Optionally trigger async refresh in background
                build_accessory_sidebar.delay()
            return Response(data)
            
        return Response({})

class ProductDetailPage(APIView):
    def get(self, request, *args, **kwargs):
        product_id = kwargs.get("product_id")
        product_type = kwargs.get("product_type")

        if product_type == "bike":
            product = BikeModel.objects.get(unique_id=product_id)
            serializer = BikeSerializer(product,context={'request': request})
        elif product_type == "accessories":
            product = AccessoriesModel.objects.get(unique_id=product_id)
            serializer = AccessoriesSerializer(product,context={'request': request})
        else:
            return Response({"error": "Invalid product type"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK) 

class ProductFilterView(APIView):
    pagination_class = CustomPagination

    def get(self, request):
        product_type = request.query_params.get("type")

        # Validate product type
        if product_type not in ["bike", "accessories"]:
            return Response(
                {"error": "type query param is required and must be 'bike' or 'accessories'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---- Cache key (INCLUDE PAGE & PAGE_SIZE) ----
        query_params = request.query_params.dict()
        query_string = json.dumps(query_params, sort_keys=True)
        cache_key = f"products_{hashlib.md5(query_string.encode()).hexdigest()}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            if product_type == "bike":
                base_qs = bike_filters(request)
            
                queryset = (
                    BikeModel.objects
                    .filter(id__in=Subquery(base_qs.values("id").distinct()))
                    .select_related(
                        "special_tag",
                        "brand",
                        "category"
                    )
                    .prefetch_related(
                        "wheel_size",
                        "material",
                        "suspension",
                        "rear_suspension_travel",
                        "sizes",
                        Prefetch(
                            "bike_colors",
                            queryset=BikeColorsModel.objects
                            .select_related("color")
                            .prefetch_related("bike_images")
                        ),
                        Prefetch(
                            "bike_spec_labels",
                            queryset=BikeSpecLabelModel.objects
                            .prefetch_related("bike_spec_values")
                        ),
                        "bike_posters",
                        "bike_downloads"
                    )
                )
                queryset = bike_filters(request).select_related(
                    "special_tag",
                    "brand",
                    "category"
                ).prefetch_related(
                    "wheel_size",
                    "material",
                    "suspension",
                    "rear_suspension_travel",
                    "sizes",
                    Prefetch(
                        "bike_colors",
                        queryset=BikeColorsModel.objects
                        .select_related("color")
                        .prefetch_related("bike_images")
                    ),
                    Prefetch(
                        "bike_spec_labels",
                        queryset=BikeSpecLabelModel.objects
                        .prefetch_related("bike_spec_values")
                    ),
                    "bike_posters",
                    "bike_downloads"
                )

            else:  # accessories
                queryset = accessories_filters(request)

        except Exception as e:
            return Response(
                {"error": f"Error applying filters: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # ---- Pagination ----
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is None:
            return Response([], status=status.HTTP_200_OK)

        # ---- Serialization ----
        serializer_class = BikeSerializer if product_type == "bike" else AccessoriesSerializer
        serializer = serializer_class(page, many=True, context={"request": request})

        response = paginator.get_paginated_response(serializer.data)

        # ---- Cache response ----
        cache.set(cache_key, response.data, timeout=60 * 10)

        return response


class SuggestedProduct(APIView):
    def get(self, request):
        BikeProducts = BikeModel.objects.filter(is_available=True,is_out_of_stock=False).order_by('-created')[:4]
        
        bike_serializer = BikeSerializer(BikeProducts, many=True,context={'request': request})
            
        return Response(bike_serializer.data, status=status.HTTP_200_OK)

class NavbarItemsAPIView(APIView):
    def get(self, request):
        query_params = request.query_params.dict()
        query_string = json.dumps(query_params, sort_keys=True)
        cache_key = f"navbar_items_{hashlib.md5(query_string.encode()).hexdigest()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # ------------------ BIKE DATA ------------------
        bike_categories = BikeCategoryModel.objects.all().order_by('-created')[:12]
        bike_items = []

        for category in bike_categories:
            items = []
            bikes = BikeModel.objects.filter(category=category).select_related('brand')

            for bike in bikes:
                bike_color = BikeColorsModel.objects.filter(bike=bike).first()
                bike_image = BikeImagesModel.objects.filter(color=bike_color).first()

                image = (
                    f"{request.scheme}://{request.get_host()}{bike_image.image.url}"
                    if bike_image else None
                )

                items.append({
                    'unique_id': bike.unique_id,
                    'product_type': bike.product_type,
                    'name': bike.name,
                    'image': image,
                    'price': bike.price,
                    'brand': bike.brand.brand_name,
                    'is_discound': bike.is_discount,
                    'discount_price': bike.discount_price,
                    'discount_percentage': bike.discount_percentage,
                })

            bike_items.append({
                'title': category.category_name,
                'image': (
                    f"{request.scheme}://{request.get_host()}{category.category_image.url}"
                    if category.category_image else None
                ),
                'items': items
            })

        # ------------------ ACCESSORIES DATA ------------------
        accessories_categories = AccessoriesCategoryModel.objects.all().order_by('-created')[:12]
        accessories_items = []

        for category in accessories_categories:
            items = []
            accessories = AccessoriesModel.objects.filter(
                sub_category__category=category
            ).select_related('brand')

            for accessory in accessories:
                images = AccessoryImagesModel.objects.filter(accessory=accessory).first()
                image = (
                    f"{request.scheme}://{request.get_host()}{images.image.url}"
                    if images else None
                )

                items.append({
                    'unique_id': accessory.unique_id,
                    'product_type': accessory.product_type,
                    'name': accessory.name,
                    'image': image,
                    'price': accessory.price,
                    'brand': accessory.brand.brand_name if accessory.brand else None,
                    'is_discound': accessory.is_discount,
                    'discount_price': accessory.discount_price,
                    'discount_percentage': accessory.discount_percentage,
                })

            accessories_items.append({
                'title': category.name,
                'image': (
                    f"{request.scheme}://{request.get_host()}{category.image.url}"
                    if category.image else None
                ),
                'items': items
            })

        response_data = {
            'bikes': bike_items,
            'accessories': accessories_items
        }

        # 🔥 Store in Redis
        cache.set(cache_key, response_data, timeout=60 * 10)

        return Response(response_data)


class ShopBuy(APIView):
    def get(self, request):
        cache_key = f"shop_buy_{hashlib.md5(request.query_params.urlencode().encode()).hexdigest()}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        bike_categories = BikeCategoryModel.objects.all().order_by('-created')[:12]
        accessories_categories = AccessoriesCategoryModel.objects.all().order_by('-created')[:12]
        
        def get_category_data(category):
            """Normalize field access across different category models"""
            if isinstance(category, BikeCategoryModel):
                name = category.category_name
                image = category.category_image
            else:  # AccessoriesCategoryModel
                name = category.name
                image = category.image
            
            return {
                'title': name,
                'image': request.build_absolute_uri(image.url) if image else None,
                'type': 'bike' if isinstance(category, BikeCategoryModel) else 'accessories'
            }
        
        categories = [
            get_category_data(category) 
            for category in chain(bike_categories, accessories_categories)
        ]
        cache.set(cache_key, categories, timeout=60 * 10)
        return Response(categories)


class FeaturdProduct(APIView):
    def get(self, request):
        bike_products = BikeModel.objects.filter(is_available=True,is_out_of_stock=False,is_featured=True).order_by('-created')[:4]
        bike_serializer = BikeSerializer(bike_products, many=True,context={'request': request})
        return Response(bike_serializer.data)

class BrandsImages(APIView):
    def get(self, request):
        cache_key = f"brands_images_{hashlib.md5(request.query_params.urlencode().encode()).hexdigest()}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        bikebrands = BikeBrandModel.objects.all()
        serializer = BikeBrandImageSerializer(bikebrands, many=True,context={'request': request})
        cache.set(cache_key, serializer.data, timeout=60 * 10)
        return Response(serializer.data)