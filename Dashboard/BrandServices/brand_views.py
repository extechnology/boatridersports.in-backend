from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from Application.permissions import IsSuperUserAuthenticated
from ..pagination import DashboardPagination
from Application.ProductServices.product_models import BikeBrandModel
from Dashboard.BrandServices.brand_serializers import BrandSerializerDashboard



class BrandListView(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    pagination_class = DashboardPagination

    def get(self, request):
        search = request.query_params.get("search", "")
        brands = BikeBrandModel.objects.all().order_by("-created")
        if search:
            brands = brands.filter(brand_name__icontains=search)
        paginator = DashboardPagination()
        paginated_qs = paginator.paginate_queryset(brands, request)
        serializer = BrandSerializerDashboard(paginated_qs, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
