from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q


import platform
import datetime
import urllib.parse
import re
import random


from .auth_models import *

from .auth_serializers import *
from .auth_emails import *

User = get_user_model()

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .auth_utils import get_user_from_request

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from django.conf import settings

# ---------------------------------------- Authentication Views --------------------------------------------------------------


class CheckUsernameView(APIView):
    def get(self, request):
        new_username = request.query_params.get("username", "").strip()


        # --- Validation checks ---
        if not new_username:
            return Response({
                "message": "Enter a username",
                "is_available": False,
                "color": "gray"
            })

        if not re.match(r'^[A-Za-z0-9_.]+$', new_username):
            return Response({
                "message": "Only letters, numbers, underscores and periods are allowed",
                "is_available": False,
                "color": "red"
            })

        if len(new_username) < 3 or len(new_username) > 20:
            return Response({
                "message": "Username must be 3 - 20 characters long",
                "is_available": False,
                "color": "red"
            })

        # --- Check directly in the database ---
        username_taken = User.objects.filter(username__iexact=new_username).exists()

        if username_taken:
            data = {
                "message": "Username already taken",
                "is_available": False,
                "color": "red"
            }
        else:
            data = {
                "message": "Username available",
                "is_available": True,
                "color": "green"
            }

        return Response(data)

class CheckIdentifierView(APIView):
    def get(self, request):
        identifier = request.query_params.get("identifier", "").strip()
        
        if not identifier:
            return Response({
                "message": "Enter an email address or phone number",
                "is_available": False,
            })

        # Identify whether it's an email or phone number
        is_email = re.match(r"[^@]+@[^@]+\.[^@]+", identifier)
        is_phone = re.match(r"^\+?\d{7,15}$", identifier)  # allows optional + and 7–15 digits

        if not (is_email or is_phone):
            return Response({
                "message": "Invalid email or phone number format",
                "is_available": False,
            })

        # Check database for existence
        if is_email:
            exists = User.objects.filter(email__iexact=identifier).exists()
            id_type = "Email"
        else:
            exists = User.objects.filter(username__iexact=identifier).exists()  # assuming phone is stored in username
            id_type = "Phone number"

        if exists:
            data = {
                "message": f"{id_type} already exists",
                "is_available": False,
            }
        else:
            data = {
                "message": f"{id_type} is available",
                "is_available": True,
            }

        return Response(data)


# @rate_limit(key='ip', rate='1/m', block=True)
class RegisterView(APIView):
   def post(self, request):
       serializer = UserRegistrationSerializer(data=request.data)
       if serializer.is_valid():
           serializer.save()
           return Response({"message": "One time password sent to your email/phone for verification"}, status=status.HTTP_201_CREATED)
       return Response({
           'message': 'Registration failed',
           'errors': serializer.errors
         }, status=status.HTTP_400_BAD_REQUEST)

# @rate_limit(key='ip', rate='1/m', block=True)
class ResendOTPView(APIView):
   def post(self, request):
       serializer = ResentOTPSerializer(data=request.data, context={'request': request})
       if serializer.is_valid():
           serializer.save()
           return Response({"message": "One time password sent to your email/phone for verification"}, status=status.HTTP_201_CREATED)
       return Response({
           'message': 'Registration failed',
           'errors': serializer.errors
         }, status=status.HTTP_400_BAD_REQUEST)
   
   
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = EmailOTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # capture the created user here
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            response = Response({
                'message': 'Account verified successfully',
                # "access_token": str(refresh.access_token),
                # "refresh_token": str(refresh)
            }, status=status.HTTP_200_OK)

            response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True, samesite='None', max_age=360000)
            response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, samesite='None', max_age=7 * 24 * 360000)
            return response
        # --- flatten the error response here ---
        errors = serializer.errors
        message = None

        if isinstance(errors, dict):
            # Try to get first field error
            for key, value in errors.items():
                if isinstance(value, list) and len(value) > 0:
                    message = value[0]
                else:
                    message = value
                break
        elif isinstance(errors, list):
            message = errors[0]
        else:
            message = str(errors)

        return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)




class LoginView(APIView):
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

        if not user or not user.check_password(password):
            return Response(
                {"message": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        response = Response({
            "message": "Login successful",
            # "access_token": str(refresh.access_token),
            # "refresh_token": str(refresh)
        }, status=status.HTTP_200_OK)

        # Set cookies
        response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True, samesite='None', max_age=360000)
        response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, samesite='None', max_age=7 * 24 * 360000)


        return response
    
    
    
    
class LogoutView(APIView):
    def post(self, request):
        response = Response({
            "message": "Logged out successfully"
        }, status=status.HTTP_200_OK)

        # Delete cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")


        return response



class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise AuthenticationFailed("Authentication credentials were not provided")

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
        except Exception:
            raise AuthenticationFailed("Invalid refresh token")

        response = Response({
            "message": "Access token refreshed",
            # "access_token": new_access_token
        }, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite='None',
            max_age=3600,
            # cross_site=True,

        )

        return response
    
class CheckLoginView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        
        print("CheckLoginView: Retrieved user:", user)

        # ✅ Step 1: Check if user is authenticated
        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            return Response({
                'is_logged_in': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'phone': getattr(user, 'phone', None),
                }
            }, status=status.HTTP_200_OK)

        # ✅ Step 2: Check token in cookies if not authenticated
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return Response({
                'is_logged_in': False,
                'message': 'No access token found'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # ✅ Step 3: Verify JWT token
        try:
            token = AccessToken(access_token)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
        except Exception as e:
            return Response({
                'is_logged_in': False,
                'message': f'Invalid or expired token: {str(e)}'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # ✅ Step 4: If token valid, return user info
        return Response({
            'is_logged_in': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': getattr(user, 'phone', None),
            }
        }, status=status.HTTP_200_OK)
        



class DirectResetPasswordView(APIView):
    def post(self, request):
        user = request.user
        password = request.data.get("password") 
        current_password = request.data.get("current_password")
        
        if current_password is None:
            return Response(
                {"error": "Current password is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not password:
            return Response(
                {"error": "Password is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user.set_password(password)
            user.save()
            password_reset_success_email(user, user.email, password)
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Password reset failed."},
                status=status.HTTP_400_BAD_REQUEST
            )   

class ResetPasswordOTPView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response = Response({
                'message': 'OTP sent successfully',
            }, status=status.HTTP_200_OK)

            return response
        
            errors = serializer.errors
            message = None
    
            if isinstance(errors, dict):
                # Try to get first field error
                for key, value in errors.items():
                    if isinstance(value, list) and len(value) > 0:
                        message = value[0]
                    else:
                        message = value
                    break
            elif isinstance(errors, list):
                message = errors[0]
            else:
                message = str(errors)

        return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendResetPasswordOTPView(APIView):
    def post(self, request):
        serializer = ResendResetPasswordOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "One time password sent to your email/phone for verification."}, status=status.HTTP_201_CREATED)
            errors = serializer.errors
            message = None
    
            if isinstance(errors, dict):
                # Try to get first field error
                for key, value in errors.items():
                    if isinstance(value, list) and len(value) > 0:
                        message = value[0]
                    else:
                        message = value
                    break
            elif isinstance(errors, list):
                message = errors[0]
            else:
                message = str(errors)
        return Response({
            'message': 'Registration failed',
            'errors': serializer.errors
          }, status=status.HTTP_400_BAD_REQUEST)
        

class VerifyResetPasswordOTPView(APIView):
    def post(self, request):
        serializer = VerifyResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
        else:
            errors = serializer.errors
            message = None

            if isinstance(errors, dict):
                for key, value in errors.items():
                    if isinstance(value, list) and len(value) > 0:
                        message = value[0]
                    else:
                        message = value
                    break
            elif isinstance(errors, list):
                message = errors[0]
            else:
                message = str(errors)

            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    def patch(self, request):
        identifier = request.data.get("identifier")
        new_password = request.data.get("new_password")
        
        if ResetPasswordOTP.objects.filter(identifier=identifier, is_verified=True).exists():
            try:
                user = User.objects.get(Q(email__iexact=identifier) | Q(phone__iexact=identifier) | Q(username__iexact=identifier))
                user.set_password(new_password)
                user.save()
                email = user.email
                password_changed_email(user, email)
                # Invalidate the OTP after use
                ResetPasswordOTP.objects.filter(identifier=identifier).delete()
                
                password_reset_success_email(user, user.email, new_password)
                
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Invalid or unverified OTP."}, status=status.HTTP_400_BAD_REQUEST)
    

    
# ---------------------------------------- End of Authentication Views --------------------------------------------------------------

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
class GoogleAuthView(APIView):
    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response({"message": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), audience="933629412968-6ap8h0f5repil5akr2reubfnl5qmbt3m.apps.googleusercontent.com")

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            google_user_id = idinfo['sub']
            email = idinfo.get('email')
            fullname = idinfo.get('name')

            user, created = User.objects.get_or_create(email=email, defaults={'username': email.split('@')[0], 'fullname': fullname})

            user.is_email_verified = True
            user.save()

            refresh = RefreshToken.for_user(user)

            response = Response({
                'message': 'Login successful',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)
            
            return response

        except ValueError as e:
            return Response({"message": f"Invalid token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

# Google Authentication Views can be added here in future
