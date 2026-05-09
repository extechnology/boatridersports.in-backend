from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from Application.ProductServices.product_models import BikeCategoryModel
from ..pagination import DashboardPagination
from .category_serializers import CategorySerializerDashboard
from Application.permissions import IsSuperUserAuthenticated
from rest_framework.views import APIView

class AllCategoriesView(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    pagination_class = DashboardPagination

    def get(self, request):
        search = request.query_params.get("search", "")
        try:
            categories = BikeCategoryModel.objects.all().order_by("-created")
            if search:
                categories = categories.filter(category_name__icontains=search)
            paginator = DashboardPagination()
            paginated_qs = paginator.paginate_queryset(categories, request)
            serializer = CategorySerializerDashboard(paginated_qs, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({
                "status": 400,
                "message": str(e),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)