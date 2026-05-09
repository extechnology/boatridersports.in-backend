from django.urls import path
from .profile_views import (
    UserProfileAPIView,
    UserAddressAPIView
)

urlpatterns = [
    path('get-user-profile/', UserProfileAPIView.as_view(), name='get-user-profile'),
    path('update-user-profile/', UserProfileAPIView.as_view(), name='update-user-profile'),
    path('add-user-address/', UserAddressAPIView.as_view(), name='add-user-address'),
    path('get-user-address/', UserAddressAPIView.as_view(), name='get-user-address'),
    path('update-user-address/', UserAddressAPIView.as_view(), name='update-user-address'),
    path('delete-user-address/', UserAddressAPIView.as_view(), name='delete-user-address'),
    
]