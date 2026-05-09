from django.urls import path,include
from .views import *

urlpatterns = [
    path('', include('Dashboard.DashboardServices.dashboard_urls')),
    path('orders/', include('Dashboard.OrdersServices.order_urls')),
    path('users/', include('Dashboard.UserServices.user_urls')),
    path('brands/', include('Dashboard.BrandServices.brand_urls')),
    path('categories/', include('Dashboard.CategoryServices.category_urls')),
    path('contact/', include('Dashboard.ContactServices.contact_urls')),
    path('products/', include('Dashboard.ProductServices.product_urls')),
    

    path('login/', SuperUserLogin.as_view(), name='superuser-login'),
    path('check-login/', CheckLoginView.as_view(), name='check-login'),
    path('logout/', LogoutView.as_view(), name='logout'),

]