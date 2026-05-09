from django.urls import path,include



urlpatterns = [
    
    path('auth/', include('Application.AuthenticationServices.auth_urls')),
    path('product/', include('Application.ProductServices.product_urls')),
    path('ui/', include('Application.UiServices.ui_urls')),
    path('cart/', include('Application.CartServices.usercart_urls')),
    path('profile/', include('Application.ProfileServices.profile_urls')),
    path('order/', include('Application.OrderServices.order_urls')),
    path('contact/', include('Application.ContactServices.contact_urls')),
]
