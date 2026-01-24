from django.urls import path
from .ui_views import *

urlpatterns = [
    path('home-slider-video/', HomeSliderVideoView.as_view(), name='home-slider-video'),
]
