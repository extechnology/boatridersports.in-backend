from django.urls import path
from .user_views import TotalUsersView

urlpatterns = [
    path('total_users/', TotalUsersView.as_view(), name='total_users'),
]