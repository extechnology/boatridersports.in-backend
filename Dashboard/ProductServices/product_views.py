from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .product_serializers import BikeSerializer,AccessorySerializer
from Application.ProductServices.product_models import BikeModel,AccessoriesModel
from Application.permissions import IsSuperUserAuthenticated
from ..pagination import DashboardPagination

class BikeListView(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    pagination_class = DashboardPagination

    def get(self, request):
        search = request.query_params.get("search", "")
        try:
            bikes = BikeModel.objects.all()
            if search:
                bikes = bikes.filter(bike_name__icontains=search)
            paginator = DashboardPagination()
            paginated_qs = paginator.paginate_queryset(bikes, request)
            serializer = BikeSerializer(paginated_qs, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({
                "status": 400,
                "message": str(e),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)


class AccessoryListView(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    pagination_class = DashboardPagination

    def get(self, request):
        search = request.query_params.get("search", "")
        try:
            accessories = AccessoriesModel.objects.all()
            if search:
                accessories = accessories.filter(name__icontains=search)
            paginator = DashboardPagination()
            paginated_qs = paginator.paginate_queryset(accessories, request)
            serializer = AccessorySerializer(paginated_qs, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({
                "status": 400,
                "message": str(e),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)