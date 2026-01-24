from django.urls import path,include



urlpatterns = [
    
    path('auth/', include('Application.AuthenticationServices.auth_urls')),
    path('product/', include('Application.ProductServices.product_urls')),
    path('ui/', include('Application.UiServices.ui_urls')),
]
