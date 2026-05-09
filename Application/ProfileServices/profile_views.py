from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from Application.AuthenticationServices.auth_utils import get_user_from_request
from .profile_models import *
from .profile_serializers import *


class UserProfileAPIView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        user_profile, created = UserProfile.objects.get_or_create(
            user=user, 
            defaults={
                'name': user.username, 
                'email': user.email
                }
            )
        user_profile_serializer = UserProfileSerializer(user_profile, context={'request': request})
        return Response(user_profile_serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = get_user_from_request(request)
        user_profile = UserProfile.objects.get(user=user)
        user_profile_serializer = UserProfileSerializer(user_profile, data=request.data, partial=True, context={'request': request})
        if user_profile_serializer.is_valid():
            user_profile_serializer.save()
            return Response(user_profile_serializer.data, status=status.HTTP_200_OK)
        return Response(user_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserAddressAPIView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        user_address = UserAddress.objects.filter(user=user)
        user_address_serializer = UserAddressSerializer(user_address, many=True)
        return Response(user_address_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = get_user_from_request(request)
        user_address_serializer = UserAddressSerializer(data=request.data)
        if user_address_serializer.is_valid():
            user_address_serializer.save(user=user)
            return Response(user_address_serializer.data, status=status.HTTP_201_CREATED)
        return Response(user_address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = get_user_from_request(request)
        user_address = UserAddress.objects.get(user=user, unique_id=request.data['unique_id'])
        user_address_serializer = UserAddressSerializer(user_address, data=request.data, partial=True)
        if user_address_serializer.is_valid():
            user_address_serializer.save()
            return Response(user_address_serializer.data, status=status.HTTP_200_OK)
        return Response(user_address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        user = get_user_from_request(request)
        user_address = UserAddress.objects.get(user=user, unique_id=request.query_params['unique_id'])
        user_address.delete()
        return Response({"message": "Address deleted successfully"}, status=status.HTTP_200_OK)