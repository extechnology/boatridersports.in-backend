from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .contact_serializers import ContactEnquirySerializer
from Application.AuthenticationServices.auth_models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .contact_utils import send_enquiry_notification

class ContactEnquiryView(APIView):

    def get_user_from_request(self, request):
        auth = JWTAuthentication()

        try:
            result = auth.authenticate(request)

            if result is not None:
                user, token = result
                return user

        except (InvalidToken, AuthenticationFailed):
            pass

        return None

    def post(self, request):
        serializer = ContactEnquirySerializer(data=request.data)

        if serializer.is_valid():
            enquiry = serializer.save()
            send_enquiry_notification(enquiry)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)