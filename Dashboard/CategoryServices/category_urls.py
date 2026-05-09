from django.urls import path
from .category_views import *

urlpatterns = [
    path('all-categories/', AllCategoriesView.as_view(), name='all-categories'),
]