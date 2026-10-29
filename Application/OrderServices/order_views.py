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
from .order_utils import order_confirmation_email, process_order_success, process_order_cancellation

from decimal import Decimal
import uuid
import json
import logging
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

def get_razorpay_client():
    key_id = str(getattr(settings, 'RAZORPAY_KEY_ID', '') or '').strip().strip('\'"')
    key_secret = str(getattr(settings, 'RAZORPAY_KEY_SECRET', '') or '').strip().strip('\'"')
    if not key_id or not key_secret:
        logger.error("RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET is missing or empty in server environment.")
        raise ValueError("Razorpay credentials are not configured on the server. Please ensure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are present in the server .env file and restart the server application.")
    return razorpay.Client(auth=(key_id, key_secret))

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
        if request.data.get('payment_gateway', '').lower() == 'razorpay':
            return RazorpayInitiateCheckoutAPIView().post(request)

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
            return_url=f"https://boatridersports.in/order-success?order_id={order_id}"
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

    def post(self, request):
        if request.data.get('razorpay_payment_id') or request.data.get('razorpay_signature'):
            return RazorpayVerifyOrderPayment().post(request)

        user = get_user_from_request(request)
        order_id = request.data.get("order_id")

        print(order_id)

        if not order_id:
            return Response(
                {
                    "status": "error",
                    "message": "Missing order_id field"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_order = UserOrdersModel.objects.get(unique_id=order_id)

        except UserOrdersModel.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Order not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        client = Cashfree(XEnvironment=Cashfree.XEnvironment)

        try:
            order_response = client.PGFetchOrder(
                x_api_version=x_api_version,
                order_id=order_id
            )

            order_data = (
                order_response.data
                if hasattr(order_response, 'data')
                else order_response
            )

            if order_data.order_status == "PAID":
                process_order_success(user_order)

                return Response(
                    {
                        "status": "success",
                        "message": "Payment verified successfully",
                        "order_status": user_order.status
                    },
                    status=status.HTTP_200_OK
                )

            else:
                reason = f"Payment not completed. Status: {order_data.order_status}"
                process_order_cancellation(user_order, reason=reason, status_name='Failed')

                return Response(
                    {
                        "status": "failed",
                        "message": reason
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:

            return Response(
                {
                    "status": "error",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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


class RazorpayInitiateCheckoutAPIView(APIView):
    permission_classes = [IsUserAuthenticated]

    def post(self, request):
        user = get_user_from_request(request)

        try:
            cart = UserCartModel.objects.get(user=user)
        except UserCartModel.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

        address_id = request.data.get('address_id')
        if not address_id:
            return Response({"error": "address_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = UserAddress.objects.get(user=user, unique_id=address_id)
        except UserAddress.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        bike_items = UserCartItemsModelBike.objects.filter(user_cart=cart)
        accessories = UserCartItemsModelAccessories.objects.filter(user_cart=cart)

        if not bike_items.exists() and not accessories.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        from Application.CartServices.usercart_serializers import UserCartModelSerializer
        cart_data = UserCartModelSerializer(cart, context={'request': request}).data
        amount = Decimal(str(cart_data['total_amount']))

        shipping_charge = cart_data.get('shipping_charge')
        if shipping_charge:
            amount += Decimal(str(shipping_charge))

        currency = request.data.get("currency", "INR")

        user_order = UserOrdersModel.objects.create(
            user=user,
            user_address=address,
            total_amount=amount,
            status='Pending',
            payment_gateway='razorpay'
        )

        order_id = user_order.unique_id

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

        # Razorpay Order Creation
        client = get_razorpay_client()
        amount_in_paise = int(amount * 100)

        customer_name = getattr(address, 'name', '') or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()

        razorpay_order_payload = {
            "amount": amount_in_paise,
            "currency": currency,
            "receipt": str(order_id),
            "notes": {
                "order_id": str(order_id),
                "user_id": str(getattr(user, 'unique_id', user.id)),
                "user_email": str(user.email),
                "customer_name": str(customer_name)
            },
            "payment_capture": 1
        }

        try:
            razorpay_order = client.order.create(data=razorpay_order_payload)
        except Exception as e:
            user_order.delete()
            logger.error("Razorpay order creation failed: %s", e)
            return Response(
                {"error": f"Payment gateway error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        user_order.razorpay_order_id = razorpay_order.get('id')
        user_order.save()

        user_order_serialized_data = UserOrdersSerializer(user_order, context={'request': request}).data

        return Response({
            'order_id': order_id,
            'razorpay_order_id': razorpay_order.get('id'),
            'amount': razorpay_order.get('amount'),
            'currency': razorpay_order.get('currency'),
            'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
            'order': user_order_serialized_data
        }, status=status.HTTP_200_OK)


class RazorpayVerifyOrderPayment(APIView):
    permission_classes = [IsUserAuthenticated]

    def post(self, request):
        user = get_user_from_request(request)
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")
        order_id = request.data.get("order_id")

        if not (razorpay_order_id or order_id) or not razorpay_payment_id or not razorpay_signature:
            return Response({
                "status": "error",
                "message": "Missing required fields: razorpay_order_id (or order_id), razorpay_payment_id, and razorpay_signature are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user_order = None
        if razorpay_order_id:
            user_order = UserOrdersModel.objects.filter(razorpay_order_id=razorpay_order_id).first()
        if not user_order and order_id:
            user_order = UserOrdersModel.objects.filter(unique_id=order_id).first()

        if not user_order:
            return Response({
                "status": "error",
                "message": "Order not found"
            }, status=status.HTTP_404_NOT_FOUND)

        client = get_razorpay_client()
        params_dict = {
            'razorpay_order_id': razorpay_order_id or user_order.razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            logger.error("Razorpay signature verification failed for order %s: %s", user_order.unique_id, e)
            process_order_cancellation(user_order, reason=f"Payment signature verification failed: {str(e)}", status_name='Failed')
            return Response({
                "status": "failed",
                "message": f"Payment signature verification failed: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fulfill order idempotently
        process_order_success(
            user_order=user_order,
            payment_id=razorpay_payment_id,
            signature=razorpay_signature
        )

        return Response({
            "status": "success",
            "message": "Payment verified successfully",
            "order_status": user_order.status
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get("X-Razorpay-Signature") or request.META.get("HTTP_X_RAZORPAY_SIGNATURE")
        raw_body = request.body.decode('utf-8') if isinstance(request.body, bytes) else str(request.body)

        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        if webhook_secret:
            if not signature:
                return Response({"error": "Missing X-Razorpay-Signature header"}, status=status.HTTP_400_BAD_REQUEST)
            client = get_razorpay_client()
            try:
                client.utility.verify_webhook_signature(raw_body, signature, webhook_secret)
            except Exception as e:
                logger.error("Razorpay webhook signature verification failed: %s", e)
                return Response({"error": f"Invalid webhook signature: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_data = json.loads(raw_body)
        except Exception:
            return Response({"error": "Invalid JSON body"}, status=status.HTTP_400_BAD_REQUEST)

        event_name = event_data.get('event')
        logger.info("Razorpay webhook event received: %s", event_name)

        payload = event_data.get('payload', {})
        order_entity = payload.get('order', {}).get('entity', {})
        payment_entity = payload.get('payment', {}).get('entity', {})

        rp_order_id = order_entity.get('id') or payment_entity.get('order_id')
        receipt = order_entity.get('receipt') or payment_entity.get('notes', {}).get('order_id')
        payment_id = payment_entity.get('id')

        user_order = None
        if rp_order_id:
            user_order = UserOrdersModel.objects.filter(razorpay_order_id=rp_order_id).first()
        if not user_order and receipt:
            user_order = UserOrdersModel.objects.filter(unique_id=receipt).first()

        if not user_order:
            logger.warning("Razorpay webhook: No matching order found for rp_order_id=%s, receipt=%s", rp_order_id, receipt)
            return Response({"status": "ignored", "message": "Order not found"}, status=status.HTTP_200_OK)

        if event_name in ['order.paid', 'payment.captured']:
            process_order_success(user_order, payment_id=payment_id)
            return Response({"status": "success", "message": "Order processed successfully"}, status=status.HTTP_200_OK)

        elif event_name == 'payment.failed':
            if not user_order.payment_status:
                process_order_cancellation(user_order, reason="Payment failed at Razorpay gateway", status_name='Failed')
            return Response({"status": "success", "message": "Order status updated to Failed"}, status=status.HTTP_200_OK)

        return Response({"status": "ignored", "message": f"Event {event_name} not handled"}, status=status.HTTP_200_OK)


class RazorpayCancelOrderAPIView(APIView):
    permission_classes = [IsUserAuthenticated]

    def post(self, request):
        user = get_user_from_request(request)
        order_id = request.data.get('order_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        reason = request.data.get('reason', 'Payment cancelled by user')

        if not order_id and not razorpay_order_id:
            return Response({
                "error": "order_id or razorpay_order_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user_order = None
        if order_id:
            user_order = UserOrdersModel.objects.filter(unique_id=order_id, user=user).first()
        if not user_order and razorpay_order_id:
            user_order = UserOrdersModel.objects.filter(razorpay_order_id=razorpay_order_id, user=user).first()

        if not user_order:
            return Response({
                "error": "Order not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if user_order.payment_status:
            return Response({
                "error": "Cannot cancel an order that has already been paid"
            }, status=status.HTTP_400_BAD_REQUEST)

        process_order_cancellation(user_order, reason=reason, status_name='Cancelled')

        return Response({
            "status": "cancelled",
            "message": "Order cancelled successfully",
            "order_id": str(user_order.unique_id),
            "order_status": user_order.status
        }, status=status.HTTP_200_OK)

        