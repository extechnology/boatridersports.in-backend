from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from itertools import chain

from Application.media_utils import build_absolute_media_url, sanitize_https_media

from .product_serializers import *
from .product_models import *

from .product_filters import bike_filters,accessories_filters
from django.db.models import Prefetch, Subquery, Q, Min, Max

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
        bikes = BikeModel.objects.all().order_by('-created')

        serializer = BikeSerializer(bikes, many=True,context={'request': request})
        return Response(serializer.data)


def _clean_unique_list(values):
    seen = set()
    result = []
    for val in values:
        if val is None:
            continue
        cleaned = str(val).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


class ProductsFilterSideBarAPIView(APIView):
    def get(self, request):
        sidebar = request.query_params.get("sidebar")
        
        if sidebar == "bike":
            data = {
                "categories": _clean_unique_list(BikeCategoryModel.objects.values_list("category_name", flat=True)),
                "brands": _clean_unique_list(BikeBrandModel.objects.values_list("brand_name", flat=True)),
                "sizes": _clean_unique_list(SizeModel.objects.values_list("size", flat=True)),
                "wheel_sizes": _clean_unique_list(WheelSizeModel.objects.values_list("wheel_size", flat=True)),
                "materials": _clean_unique_list(MaterialModel.objects.values_list("material", flat=True)),
                "suspensions": _clean_unique_list(SuspensionModel.objects.values_list("suspension", flat=True)),
                "rearSuspensionTravel": _clean_unique_list(
                    RearSuspensionTravelModel.objects.values_list("rear_suspension_travel", flat=True)
                ),
                "colors": [
                    {
                        "name": c.color_name,
                        "code": list(filter(None, [c.color_code, c.color_code_2]))
                    }
                    for c in ColorModel.objects.all()
                ],
                "product_type": "bike",
                "special_tags": _clean_unique_list(SpecialTagModel.objects.values_list("tag_name", flat=True))
            }
            return Response(data)
            
        elif sidebar == "accessories":
            acc_qs = AccessoriesModel.objects.all()

            price_agg = acc_qs.aggregate(
                min_price=models.Min('price'),
                max_price=models.Max('price')
            )
            min_p = float(price_agg["min_price"]) if price_agg["min_price"] is not None else 0.0
            max_p = float(price_agg["max_price"]) if price_agg["max_price"] is not None else 0.0

            brands_list = _clean_unique_list(
                BikeBrandModel.objects.filter(accessories__isnull=False)
                .values_list("brand_name", flat=True)
            ) or _clean_unique_list(BikeBrandModel.objects.values_list("brand_name", flat=True))

            data = {
                "product_type": "accessories",
                "brands": brands_list,
                "categories": _clean_unique_list(
                    AccessoriesCategoryModel.objects.values_list("name", flat=True)
                ),
                "sub_categories": _clean_unique_list(
                    AccessoriesSubCategoryModel.objects.values_list("name", flat=True)
                ),
                "model_numbers": _clean_unique_list(
                    acc_qs.exclude(model_no__isnull=True).exclude(model_no="")
                    .values_list("model_no", flat=True)
                ),
                "model_names": _clean_unique_list(
                    acc_qs.exclude(model_name__isnull=True).exclude(model_name="")
                    .values_list("model_name", flat=True)
                ),
                "speeds": _clean_unique_list(
                    acc_qs.exclude(speed__isnull=True).exclude(speed="")
                    .values_list("speed", flat=True)
                ),
                "tire_types": _clean_unique_list(
                    acc_qs.exclude(tire_type__isnull=True).exclude(tire_type="")
                    .values_list("tire_type", flat=True)
                ),
                "hub_widths": _clean_unique_list(
                    acc_qs.exclude(hub_width__isnull=True).exclude(hub_width="")
                    .values_list("hub_width", flat=True)
                ),
                "valve_types": _clean_unique_list(
                    acc_qs.exclude(valve_type__isnull=True).exclude(valve_type="")
                    .values_list("valve_type", flat=True)
                ),
                "sizes": _clean_unique_list(
                    acc_qs.exclude(size__isnull=True).exclude(size="")
                    .values_list("size", flat=True)
                ),
                "ml": _clean_unique_list(
                    acc_qs.exclude(ml__isnull=True).exclude(ml="")
                    .values_list("ml", flat=True)
                ),
                "colors": _clean_unique_list(
                    acc_qs.exclude(color__isnull=True).exclude(color="")
                    .values_list("color", flat=True)
                ),
                "bike_mounted_types": _clean_unique_list(
                    acc_qs.exclude(bike_mounted_type__isnull=True).exclude(bike_mounted_type="")
                    .values_list("bike_mounted_type", flat=True)
                ),
                "materials": _clean_unique_list(
                    acc_qs.exclude(material__isnull=True).exclude(material="")
                    .values_list("material", flat=True)
                ),
                "warranties": _clean_unique_list(
                    acc_qs.exclude(warranty__isnull=True).exclude(warranty="")
                    .values_list("warranty", flat=True)
                ),
                "price_range": {
                    "min_price": min_p,
                    "max_price": max_p
                },
                "mrp_range": {
                    "min_price": min_p,
                    "max_price": max_p
                },
                "special_tags": _clean_unique_list(
                    SpecialTagModel.objects.values_list("tag_name", flat=True)
                )
            }
            return Response(data)
            
        return Response({})

from django.core.exceptions import ValidationError

class ProductDetailPage(APIView):
    def get(self, request, *args, **kwargs):
        product_id = kwargs.get("product_id")
        product_type = kwargs.get("product_type")

        try:
            if product_type == "bike":
                if str(product_id).isdigit():
                    product = BikeModel.objects.get(id=int(product_id))
                else:
                    product = BikeModel.objects.get(unique_id=product_id)
                serializer = BikeSerializer(product, context={'request': request})
            elif product_type == "accessories":
                if str(product_id).isdigit():
                    product = AccessoriesModel.objects.get(id=int(product_id))
                else:
                    product = AccessoriesModel.objects.get(unique_id=product_id)
                serializer = AccessoriesSerializer(product, context={'request': request})
            else:
                return Response({"error": "Invalid product type"}, status=status.HTTP_400_BAD_REQUEST)
        except (BikeModel.DoesNotExist, AccessoriesModel.DoesNotExist, ValidationError, ValueError):
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

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

        # ---- Cache key (INCLUDE PAGE & PAGE_SIZE, MULTI-VAL PARAMS) ----
        query_param_items = [(k, sorted(request.query_params.getlist(k))) for k in sorted(request.query_params.keys())]
        query_string = json.dumps(query_param_items, sort_keys=True)
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
        cache_key = f"navbar_items_{hashlib.md5(f'{query_string}_{request.scheme}'.encode()).hexdigest()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(sanitize_https_media(cached_data))

        # ------------------ BIKE DATA ------------------
        bike_categories = BikeCategoryModel.objects.all().order_by('-created')
        bike_items = []

        for category in bike_categories:
            items = []
            bikes = BikeModel.objects.filter(category=category).select_related('brand')

            for bike in bikes:
                bike_color = BikeColorsModel.objects.filter(bike=bike).first()
                bike_image = BikeImagesModel.objects.filter(color=bike_color).first()

                image = (
                    build_absolute_media_url(request, bike_image.image.url)
                    if bike_image else None
                )

                items.append({
                    'unique_id': str(bike.unique_id),
                    'product_type': bike.product_type,
                    'name': bike.name,
                    'image': image,
                    'price': bike.price,
                    'brand': bike.brand.brand_name if bike.brand else None,
                    'is_discound': bike.is_discount,
                    'is_discount': bike.is_discount,
                    'discount_price': bike.discount_price,
                    'discount_percentage': bike.discount_percentage,
                })

            bike_items.append({
                'title': category.category_name,
                'image': (
                    build_absolute_media_url(request, category.category_image.url)
                    if category.category_image else None
                ),
                'items': items
            })

        # ------------------ ACCESSORIES DATA ------------------
        accessories_categories = AccessoriesCategoryModel.objects.all().order_by('-created')
        accessories_items = []

        def _serialize_accessory_item(accessory):
            images = AccessoryImagesModel.objects.filter(accessory=accessory).first()
            image = (
                build_absolute_media_url(request, images.image.url)
                if images and images.image else None
            )
            cat_name = (
                accessory.sub_category.category.name
                if (accessory.sub_category and accessory.sub_category.category)
                else None
            )
            subcat_name = accessory.sub_category.name if accessory.sub_category else None

            return {
                'unique_id': str(accessory.unique_id),
                'product_type': accessory.product_type,
                'name': accessory.name,
                'image': image,
                'price': accessory.price,
                'brand': accessory.brand.brand_name if accessory.brand else None,
                'category': cat_name,
                'sub_category': subcat_name,
                'short_description': accessory.short_description,
                'is_discound': accessory.is_discount,
                'is_discount': accessory.is_discount,
                'discount_price': accessory.discount_price,
                'discount_percentage': accessory.discount_percentage,
            }

        # Process Categories only
        for category in accessories_categories:
            cat_name = category.name.strip()

            accessories = AccessoriesModel.objects.filter(
                Q(sub_category__category=category) |
                Q(sub_category__name__iexact=cat_name) |
                Q(sub_category__name__icontains=cat_name)
            ).select_related('brand', 'sub_category', 'sub_category__category').distinct()

            items = [_serialize_accessory_item(acc) for acc in accessories]

            accessories_items.append({
                'title': category.name,
                'image': (
                    build_absolute_media_url(request, category.image.url)
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
            return Response(sanitize_https_media(cached_data), status=status.HTTP_200_OK)
        bike_categories = BikeCategoryModel.objects.all().order_by('-created')
        accessories_categories = AccessoriesCategoryModel.objects.all().order_by('-created')
        
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
                'image': build_absolute_media_url(request, image.url) if image else None,
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
    
