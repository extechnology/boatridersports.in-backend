from django.urls import path
from .event_dashboard_views import (
    DashboardEventListCreateView,
    DashboardEventDetailView,
    DashboardEventRegistrationsView,
    DashboardRegistrationStatusUpdateView,
    DashboardEventExportCSVView
)

urlpatterns = [
    # Event list & creation
    path('', DashboardEventListCreateView.as_view(), name='dashboard-event-list-create'),

    # Registration status update (placed before <str:id> to prevent greedy match)
    path('registrations/<str:id>/status/', DashboardRegistrationStatusUpdateView.as_view(), name='dashboard-registration-status-update'),

    # Single event management
    path('<str:id>/', DashboardEventDetailView.as_view(), name='dashboard-event-detail'),
    path('<str:id>/registrations/', DashboardEventRegistrationsView.as_view(), name='dashboard-event-registrations'),
    path('<str:id>/export-csv/', DashboardEventExportCSVView.as_view(), name='dashboard-event-export-csv'),
]

