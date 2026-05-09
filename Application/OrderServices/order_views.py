from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from Application.AuthenticationServices.auth_utils import get_user_from_request
from Application.permissions import IsUserAuthenticated
from .order_models import UserOrdersModel,BikeOrderItems,AccessoriesOrderItems
from .order_serializers import (
    UserOrdersSerializer,
    BikeOrdeItemsSerializer,
    AccessoriesOrdeItemsSerializer
)
from Application.ProductServices.product_models import (
    BikeModel,
    AccessoriesModel
)
from .order_utils import order_confirmation_email

from decimal import Decimal
import uuid
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.api_client import Cashfree
from cashfree_pg.models.customer_details import CustomerDetails
from cashfree_pg.models.order_meta import OrderMeta

Cashfree.XClientId = settings.CASHFREE_CLIENT_ID
Cashfree.XClientSecret = settings.CASHFREE_CLIENT_SECRET
Cashfree.XEnvironment = Cashfree.XSandbox
x_api_version = "2023-08-01"

from Application.CartServices.usercart_models import (
    UserCartItemsModelAccessories,
    UserCartItemsModelBike,
    UserCartModel
)

from Application.ProfileServices.profile_models import (
    UserAddress
)

class InitaiteChcekOutAPIview(APIView):
    permission_classes = [IsUserAuthenticated]
    
    def post(self, request):
        user = get_user_from_request(request)
        
        try:
            cart = UserCartModel.objects.get(user=user)
        except UserCartModel.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
            
        address_id = request.data.get('address_id')
        try:
            address = UserAddress.objects.get(user=user, unique_id=address_id)
        except UserAddress.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        bike_items = UserCartItemsModelBike.objects.filter(user_cart=cart)
        accessories = UserCartItemsModelAccessories.objects.filter(user_cart=cart)
        
        from Application.CartServices.usercart_serializers import UserCartModelSerializer
        cart_data = UserCartModelSerializer(cart, context={'request': request}).data
        amount = cart_data['total_amount']
        
        shipping_charge = cart_data['shipping_charge']
        if shipping_charge:
            amount += shipping_charge

        currency = request.data.get("currency", "INR")

        if not bike_items.exists() and not accessories.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        user_order = UserOrdersModel.objects.create(
            user=user,
            user_address=address,
            total_amount=amount,
            status='Pending'
        )
        
        order_id = user_order.unique_id
        customer_id = f"cust_{user.unique_id}"  

        customerDetails = CustomerDetails(
            customer_id=customer_id,
            customer_name=address.name,
            customer_email=user.email,
            customer_phone=address.phone_number
        )

        orderMeta = OrderMeta(
            return_url=f"http://localhost:3000/order-success?order_id={order_id}"
        )

        pg_order_amount = float(amount)
        # if Cashfree.XEnvironment == Cashfree.XSandbox and pg_order_amount > 50000:
        #     pg_order_amount = 1.0  # Bypass sandbox order amount limit

        createOrderRequest = CreateOrderRequest(
            order_id=order_id,
            order_amount=pg_order_amount,
            order_currency=currency,
            customer_details=customerDetails,
            order_meta=orderMeta
        )

        print("createOrderRequest", createOrderRequest)

        client = Cashfree(XEnvironment=Cashfree.XEnvironment)

        try:
            create_order_response = client.PGCreateOrder(
                create_order_request=createOrderRequest,
                x_api_version=x_api_version
            )
        except Exception as e:
            user_order.delete()
            return Response({"error": f"Payment gateway error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment_session_id = create_order_response.data.payment_session_id if hasattr(create_order_response, 'data') else create_order_response.payment_session_id

        bike_order_items = [
            BikeOrderItems(
                bike=item.bike,
                quantity=item.quantity,
                price=item.bike.price,
                subtotal=item.bike.price * item.quantity,
                color=item.color,
                size=item.size,
                order=user_order
            ) for item in bike_items
        ]

        accessory_order_items = [
            AccessoriesOrderItems(
                accessory=item.accessory,
                quantity=item.quantity,
                price=item.accessory.price,
                subtotal=item.accessory.price * item.quantity,
                order=user_order
            ) for item in accessories
        ]

        if bike_order_items:
            BikeOrderItems.objects.bulk_create(bike_order_items)
        if accessory_order_items:
            AccessoriesOrderItems.objects.bulk_create(accessory_order_items)

        total_items = sum(item.quantity for item in bike_items) + sum(item.quantity for item in accessories)
        user_order.total_items = total_items
        user_order.save()

        user_order_serialized_data = UserOrdersSerializer(user_order, context={'request': request}).data

        return Response({
            'order_id': order_id,
            'payment_session_id': payment_session_id,
            'order': user_order_serialized_data
        }, status=status.HTTP_200_OK)


class VerifyOrderPayment(APIView):
    permission_classes = [IsUserAuthenticated]

    def post(self,request):
        user = get_user_from_request(request)
        order_id = request.data.get("order_id")
        
        print(order_id)
        
        if not order_id:
            return Response({"status": "error", "message": "Missing order_id field"}, status=status.HTTP_400_BAD_REQUEST)


        try:
            user_order = UserOrdersModel.objects.get(unique_id=order_id)
        except UserOrdersModel.DoesNotExist:
            return Response({"status": "error", "message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        client = Cashfree(XEnvironment=Cashfree.XEnvironment)

        try:
            order_response = client.PGFetchOrder(
                x_api_version=x_api_version,
                order_id=order_id
            )
            
            order_data = order_response.data if hasattr(order_response, 'data') else order_response
            
            if order_data.order_status == "PAID":
                user_order.status = 'Processing'
                user_order.payment_status = True
                user_order.save()
                bike_id  = BikeOrderItems.objects.filter(order=order_id).values('bike_id')
                if bike_id:
                    bike = BikeModel.objects.filter(unique_id__in=bike_id).first()
                    bike.stock -= 1
                    bike.save()
                accessory_id  = AccessoriesOrderItems.objects.filter(order=order_id).values('accessory_id')
                if accessory_id:
                    accessory = AccessoriesModel.objects.filter(unique_id__in=accessory_id).first()
                    accessory.stock -= 1
                    accessory.save()
        
        
                order_confirmation_email(user_order)
                
                try:
                    cart = UserCartModel.objects.get(user=user)
                    cart.delete()
                except UserCartModel.DoesNotExist:
                    pass
                
                return Response({"status": "success", "message": "Payment verified successfully", "order_status": user_order.status}, status=status.HTTP_200_OK)
            else:
                user_order.status = 'Failed'
                user_order.save()
                return Response({"status": "failed", "message": f"Payment not completed. Status: {order_data.order_status}"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserOrders(APIView):
    permission_classes = [IsUserAuthenticated]

    def get(self, request):
        user = get_user_from_request(request)
        try:
            orders = UserOrdersModel.objects.filter(user=user)
        except UserOrdersModel.DoesNotExist:
            return Response({"error": "Orders not found"}, status=status.HTTP_404_NOT_FOUND)
        
        orders_serialized = UserOrdersSerializer(orders, many=True, context={'request': request}).data
        return Response(orders_serialized, status=status.HTTP_200_OK)
        