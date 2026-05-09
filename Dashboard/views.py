from rest_framework.decorators import permission_classes
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Q
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
# Create your views here.

from Application.AuthenticationServices.auth_models import User
from Application.AuthenticationServices.auth_utils import get_user_from_request

from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken


class SuperUserLogin(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"message": "Identifier and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(
            Q(username=identifier) | Q(email=identifier) | Q(phone=identifier)
        ).first()

        if not user or not user.check_password(password) or not user.is_superuser == True:
            return Response(
                {"message": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        print(user.username)

        response = Response({
            "message": "Login successful",
            # "access_token": str(refresh.access_token),
            # "refresh_token": str(refresh)
        }, status=status.HTTP_200_OK)

        # Set cookies
        response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True, samesite='None', max_age=360000)
        response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, samesite='None', max_age=7 * 24 * 360000)


        return response
    

class CheckLoginView(APIView):
    def get(self, request):
        user = get_user_from_request(request)

        # ✅ Step 1 & 2: Check if user is authenticated (via request or cookies)
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            access_token = request.COOKIES.get('access_token')
            if not access_token:
                return Response({
                    'is_logged_in': False,
                    'message': 'No access token found'
                }, status=status.HTTP_401_UNAUTHORIZED)
            try:
                # ✅ Step 3: Verify JWT token
                token = AccessToken(access_token)
                user = User.objects.get(id=token['user_id'])
            except Exception as e:
                return Response({
                    'is_logged_in': False,
                    'message': f'Invalid or expired token: {str(e)}'
                }, status=status.HTTP_401_UNAUTHORIZED)


        return Response({
            'is_logged_in': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': getattr(user, 'phone', None),

            }
        }, status=status.HTTP_200_OK)


    
class LogoutView(APIView):
    def post(self, request):

        response = Response({
            "message": "Logged out successfully"
        }, status=status.HTTP_200_OK)

        # Delete cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")


        return response