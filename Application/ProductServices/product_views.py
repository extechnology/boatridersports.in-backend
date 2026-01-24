from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination

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


class BikesFilteredAPIView(APIView):
    pagination_class = CustomPagination
    filterset_class = BikeFilter

    def get(self, request, *args, **kwargs):
        # 1️⃣ Build unique cache key from query params
        query_params = request.query_params.dict()
        query_string = json.dumps(query_params, sort_keys=True)
        cache_key = "bikes_filtered_" + hashlib.md5(query_string.encode()).hexdigest()

        # 2️⃣ Try Redis first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # 3️⃣ Apply filters manually
        queryset = BikeModel.objects.all()
        filterset = self.filterset_class(request.GET, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs

        # 4️⃣ Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = BikeSerializer(page, many=True,context={'request': request})
            response_data = paginator.get_paginated_response(serializer.data).data
        else:
            serializer = BikeSerializer(queryset, many=True,context={'request': request})
            response_data = serializer.data

        # 5️⃣ Store in Redis (10 minutes)
        cache.set(cache_key, response_data, timeout=60 * 10)

        return Response(response_data, status=status.HTTP_200_OK)



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

class ProductsFilteredAPIView(APIView):
    pagination_class = CustomPagination  # reuse same pagination

    def get(self, request, *args, **kwargs):
        product_type = request.query_params.get("type")
        # category = request.GET.getlist('category')
        # print(category)

        # 🔴 Validate type
        if product_type not in ["bike", "accessories"]:
            return Response(
                {"error": "type query param must be 'bike' or 'accessory'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1️⃣ Build cache key (type + filters)
        query_params = request.query_params.dict()
        query_string = json.dumps(query_params, sort_keys=True)
        cache_key = f"{product_type}_filtered_" + hashlib.md5(query_string.encode()).hexdigest()

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # 2️⃣ Select model, filter, serializer dynamically
        if product_type == "bike":
            queryset = BikeModel.objects.all()
            filterset_class = BikeFilter
            serializer_class = BikeSerializer

        elif product_type == "accessories":  # accessory
            queryset = AccessoriesModel.objects.all()
            filterset_class = AccessoriesFilter
            serializer_class = AccessoriesSerializer

        # 3️⃣ Apply filters
        filterset = filterset_class(request.GET, queryset=queryset,request=request)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs

        # 4️⃣ Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = serializer_class(
                page, many=True, context={"request": request}
            )
            response_data = paginator.get_paginated_response(serializer.data).data
        else:
            serializer = serializer_class(
                queryset, many=True, context={"request": request}
            )
            response_data = serializer.data

        # 5️⃣ Cache result (10 minutes)
        cache.set(cache_key, response_data, timeout=60 * 10)

        return Response(response_data, status=status.HTTP_200_OK)

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

class CustomProductFilterView(APIView):
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