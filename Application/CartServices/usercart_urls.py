from django.urls import path
from .usercart_views import (
    AddUserCartItems,
    UserCartAPIView,
    DeleteUserCartItems,
    UpdateCartItem,
    DeleteAllCartItems
)
urlpatterns = [
    path('add-user-cart-items/', AddUserCartItems.as_view(), name='add-user-cart-items'),
    path('user-cart/', UserCartAPIView.as_view(), name='user-cart'),
    path('delete-user-cart-items/', DeleteUserCartItems.as_view(), name='delete-user-cart-items'),
    path('update-cart-item/', UpdateCartItem.as_view(), name='update-cart-item-quantity'),
    path('delete-all-cart-items/', DeleteAllCartItems.as_view(), name='delete-all-cart-items'),
]