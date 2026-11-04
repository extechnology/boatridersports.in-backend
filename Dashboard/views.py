from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from Application.AuthenticationServices.auth_models import User


class SuperUserLogin(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = (
            request.data.get("identifier") or
            request.data.get("username") or
            request.data.get("email") or
            request.data.get("phone")
        )
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"message": "Identifier and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        identifier = str(identifier).strip()
        password = str(password).strip()

        user = User.objects.filter(
            Q(username__iexact=identifier) |
            Q(email__iexact=identifier) |
            Q(phone=identifier)
        ).first()

        if not user or not user.check_password(password) or not (user.is_superuser or user.is_staff):
            return Response(
                {"message": "Invalid credentials or unauthorized account"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        response = Response({
            "message": "Login successful",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": getattr(user, 'phone', None),
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
            }
        }, status=status.HTTP_200_OK)

        # Set cookies (support cross-site HTTPS requests)
        cookie_kwargs = {
            "httponly": True,
            "secure": True,
            "samesite": "None",
        }
        response.set_cookie("access_token", str(refresh.access_token), max_age=360000, **cookie_kwargs)
        response.set_cookie("refresh_token", str(refresh), max_age=7 * 24 * 360000, **cookie_kwargs)

        return response


class CheckLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        token_str = None

        # 1. Check Authorization header: Bearer <token>
        auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token_str = auth_header.split(' ')[1].strip()

        # 2. Check cookies
        if not token_str:
            token_str = request.COOKIES.get('access_token')

        if not token_str:
            return Response({
                'is_logged_in': False,
                'message': 'No access token found'
            }, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = AccessToken(token_str)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
            if not user.is_active or not (user.is_superuser or user.is_staff):
                return Response({
                    'is_logged_in': False,
                    'message': 'User is not an active staff/superuser'
                }, status=status.HTTP_403_FORBIDDEN)

            return Response({
                'is_logged_in': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'phone': getattr(user, 'phone', None),
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff,
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'is_logged_in': False,
                'message': f'Invalid or expired token: {str(e)}'
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({
            "message": "Logged out successfully"
        }, status=status.HTTP_200_OK)

        # Delete cookies
        response.delete_cookie("access_token", samesite="None")
        response.delete_cookie("refresh_token", samesite="None")

        return response
