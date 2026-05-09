from .contact_serializers import ContactEnquirySerializer
from Application.ContactServices.contact_models import ContactEnquiryModel
from ..pagination import DashboardPagination
from Application.permissions import IsSuperUserAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ContactEnquiryViewDashboard(APIView):
    permission_classes = [IsSuperUserAuthenticated]

    def get(self, request):
        search = request.query_params.get('search', '')
        try:
            enquiries = ContactEnquiryModel.objects.all().order_by('-created')
            if search:
                enquiries = enquiries.filter(name__icontains=search)   

            paginator = DashboardPagination()
            page = paginator.paginate_queryset(enquiries, request)

            serializer = ContactEnquirySerializer(page, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
