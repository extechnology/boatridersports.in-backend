from django.urls import path
from .auth_views import *


urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('resend-otp/', ResendOTPView.as_view(), name='resent-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('check-login/', CheckLoginView.as_view(), name='check-login'),
    
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),
    path('check-identifier/', CheckIdentifierView.as_view(), name='check-identifier'),
    
    path('password/reset/direct/', DirectResetPasswordView.as_view(), name='direct-reset-password'),
    path('password/reset/otp/', ResetPasswordOTPView.as_view(), name='reset-password'),
    path('password/reset/otp/resent/', ResendResetPasswordOTPView.as_view(), name='reset-password-confirm'),
    path('password/reset/otp/verify/', VerifyResetPasswordOTPView.as_view(), name='reset-password-verify'),
    path('password/change/', ChangePasswordView.as_view(), name='change-password'),
    
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    
]