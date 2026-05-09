from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Application.AuthenticationServices.auth_utils import get_user_from_request
from Application.permissions import IsUserAuthenticated
from django.conf import settings

from .usercart_models import *
from .usercart_serializers import *

from Application.ProductServices.product_models import(
    BikeModel,
    AccessoriesModel,
    BikeColorsModel,
    BikeSizesModel,
    SizeModel,
    ColorModel
    )

import uuid
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.api_client import Cashfree
from cashfree_pg.models.customer_details import CustomerDetails
from cashfree_pg.models.order_meta import OrderMeta

Cashfree.XClientId = settings.CASHFREE_CLIENT_ID
Cashfree.XClientSecret = settings.CASHFREE_CLIENT_SECRET
Cashfree.XEnvironment = Cashfree.XSandbox
x_api_version = "2023-08-01"


class AddUserCartItems(APIView):
    permission_classes = [IsUserAuthenticated]
    def post(self, request):
        user = get_user_from_request(request)
        product_type = request.data.get('product_type')
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        # Get or create the user's cart
        cart, created = UserCartModel.objects.get_or_create(user=user)

        if product_type == 'bike':
            size_str = request.data.get('size')
            color_str = request.data.get('color')
            
            try:
                bike = BikeModel.objects.get(unique_id=product_id)
                size = SizeModel.objects.get(size=size_str)
                color = ColorModel.objects.get(color_name=color_str)
                bike_color = BikeColorsModel.objects.get(bike=bike, color=color)

            except (BikeModel.DoesNotExist, SizeModel.DoesNotExist, ColorModel.DoesNotExist, BikeColorsModel.DoesNotExist):
                return Response({"error": "Invalid bike, size, or color"}, status=status.HTTP_400_BAD_REQUEST)

            cart_item, item_created = UserCartItemsModelBike.objects.get_or_create(
                user_cart=cart,
                bike=bike,
                size=size,
                color=bike_color,
                defaults={'quantity': quantity}
            )
            if not item_created:
                cart_item.quantity += quantity
                cart_item.save()

        elif product_type == 'accessories':
            try:
                accessory = AccessoriesModel.objects.get(unique_id=product_id)
            except AccessoriesModel.DoesNotExist:
                return Response({"error": "Invalid accessory"}, status=status.HTTP_400_BAD_REQUEST)

            cart_item, item_created = UserCartItemsModelAccessories.objects.get_or_create(
                user_cart=cart,
                accessory=accessory,
                defaults={'quantity': quantity}
            )
            
            if not item_created:
                cart_item.quantity += quantity
                cart_item.save()
        else:
            return Response({"error": "Invalid product type"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Item added to cart successfully"}, status=status.HTTP_200_OK)

    
class UserCartAPIView(APIView):
    permission_classes = [IsUserAuthenticated]
    def get(self, request):
        user = get_user_from_request(request)
        try:
            cart = UserCartModel.objects.get(user=user)
        except UserCartModel.DoesNotExist:
            return Response({"products": []}, status=status.HTTP_200_OK)
        return Response(UserCartModelSerializer(cart, context = {'request':request}).data)

class DeleteUserCartItems(APIView):
    permission_classes = [IsUserAuthenticated]
    def delete(self, request):
        user = get_user_from_request(request)
        cart_item_id = request.query_params.get('cart_item_id')
        product_type = request.query_params.get('product_type')
        try:
            if product_type == 'bike':
                cart_item = UserCartItemsModelBike.objects.get(id=cart_item_id, user_cart__user=user)
                cart_item.delete()
                return Response({"message": "Cart item deleted successfully"}, status=status.HTTP_200_OK)
            elif product_type == 'accessories':
                cart_item = UserCartItemsModelAccessories.objects.get(id=cart_item_id, user_cart__user=user)
                cart_item.delete()
                return Response({"message": "Cart item deleted successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid product type"}, status=status.HTTP_400_BAD_REQUEST)
        except (UserCartItemsModelBike.DoesNotExist, UserCartItemsModelAccessories.DoesNotExist):
            return Response({"error": "Cart item not found"}, status=status.HTTP_400_BAD_REQUEST)

class UpdateCartItem(APIView):
    permission_classes = [IsUserAuthenticated]
    def patch(self, request):
        user = get_user_from_request(request)
        cart_item_id = request.data.get('cart_item_id')
        quantity = request.data.get('quantity')
        product_type = request.data.get('product_type')
        try:
            if product_type == 'bike':
                product_color = request.data.get('product_color')
                product_size = request.data.get('product_size')
                
                try:
                    cart_item = UserCartItemsModelBike.objects.get(id=cart_item_id, user_cart__user=user)
                except UserCartItemsModelBike.DoesNotExist:
                    return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
                
                if product_color:
                    try:
                        bike_colors = BikeColorsModel.objects.get(bike=cart_item.bike, color__color_name=product_color)
                        cart_item.color = bike_colors
                    except BikeColorsModel.DoesNotExist:
                        return Response({"error": "Invalid product color"}, status=status.HTTP_400_BAD_REQUEST)
                    except BikeColorsModel.MultipleObjectsReturned:
                        # Fallback if there are duplicate colors for the same bike
                        cart_item.color = BikeColorsModel.objects.filter(bike=cart_item.bike, color__color_name=product_color).first()
                        
                if product_size:
                    try:
                        bike_sizes = SizeModel.objects.get(size=product_size)
                        cart_item.size = bike_sizes
                    except SizeModel.DoesNotExist:
                        return Response({"error": "Invalid product size"}, status=status.HTTP_400_BAD_REQUEST)
                
                if quantity is not None:
                    cart_item.quantity = quantity
                    
                cart_item.save()
                return Response({"message": "Cart item updated successfully"}, status=status.HTTP_200_OK)
            elif product_type == 'accessories':
                cart_item = UserCartItemsModelAccessories.objects.get(id=cart_item_id, user_cart__user=user)
                if quantity is not None:
                    cart_item.quantity = quantity
                cart_item.save()
                return Response({"message": "Cart item updated successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid product type"}, status=status.HTTP_400_BAD_REQUEST)
        except (UserCartItemsModelBike.DoesNotExist, UserCartItemsModelAccessories.DoesNotExist):
            return Response({"error": "Cart item not found"}, status=status.HTTP_400_BAD_REQUEST)
        

class DeleteAllCartItems(APIView):
    permission_classes = [IsUserAuthenticated]
    def delete(self, request):
        user = get_user_from_request(request)
        cart = UserCartModel.objects.get(user=user)
        cart.user_cart_bike_items.all().delete()
        cart.user_cart_accessory_items.all().delete()
        return Response({"message": "Cart deleted successfully"}, status=status.HTTP_200_OK)


