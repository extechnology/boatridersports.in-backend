from django.urls import path
from .event_dashboard_views import (
    DashboardEventListCreateView,
    DashboardEventDetailView,
    DashboardEventRegistrationsView,
    DashboardRegistrationStatusUpdateView,
    DashboardEventExportCSVView,
    DashboardTotalEventRegistrationsView,
    DashboardAllRegistrationsExcelExportView,
)

urlpatterns = [
    # Global registrations & total data export across ALL events (before <str:id>/ to prevent greedy match)
    path('registrations/all/', DashboardTotalEventRegistrationsView.as_view(), name='dashboard-all-registrations'),
    path('registrations/', DashboardTotalEventRegistrationsView.as_view(), name='dashboard-registrations-list'),
    path('total-registrations/', DashboardTotalEventRegistrationsView.as_view(), name='dashboard-total-registrations'),
    path('export-excel/', DashboardAllRegistrationsExcelExportView.as_view(), name='dashboard-events-export-excel'),
    path('export-csv/', DashboardAllRegistrationsExcelExportView.as_view(), name='dashboard-events-export-csv'),

    # Registration status update
    path('registrations/<str:id>/status/', DashboardRegistrationStatusUpdateView.as_view(), name='dashboard-registration-status-update'),

    # Event list & creation
    path('', DashboardEventListCreateView.as_view(), name='dashboard-event-list-create'),

    # Single event management
    path('<str:id>/', DashboardEventDetailView.as_view(), name='dashboard-event-detail'),
    path('<str:id>/registrations/', DashboardEventRegistrationsView.as_view(), name='dashboard-event-registrations'),
    path('<str:id>/export-csv/', DashboardEventExportCSVView.as_view(), name='dashboard-event-export-csv'),
    path('<str:id>/export-excel/', DashboardEventExportCSVView.as_view(), name='dashboard-event-export-excel-single'),
]

