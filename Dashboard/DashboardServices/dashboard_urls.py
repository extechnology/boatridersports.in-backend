from django.urls import path
from .dashboard_views import *

urlpatterns = [
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path('resend-orders/',RecentOrdersView.as_view(), name="resend-orders")
]