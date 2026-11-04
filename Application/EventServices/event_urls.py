from django.urls import path
from .event_views import EventListView, EventDetailView, EventRegistrationView

urlpatterns = [
    path('', EventListView.as_view(), name='event-list'),
    path('register/', EventRegistrationView.as_view(), name='event-register'),
    path('<str:id_or_slug>/', EventDetailView.as_view(), name='event-detail'),
]

