import json
import hmac
import hashlib
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from Application.AuthenticationServices.auth_models import User
from Application.ProfileServices.profile_models import UserAddress
from Application.ProductServices.product_models import (
    BikeModel,
    BikeCategoryModel,
    BikeBrandModel,
    ColorModel,
    SizeModel,
    BikeColorsModel,
    SpecialTagModel,
)
from Application.CartServices.usercart_models import (
    UserCartModel,
    UserCartItemsModelBike,
)
from Application.OrderServices.order_models import (
    UserOrdersModel,
    BikeOrderItems,
)
from razorpay.errors import SignatureVerificationError


class RazorpayIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='9876543210',
            password='Password123!'
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

        # Create address
        self.address = UserAddress.objects.create(
            user=self.user,
            name='Test Buyer',
            phone_number='9876543210',
            address='123 Test Street',
            city='Test City',
            state='Kerala',
            pincode='682001',
            address_type='Home'
        )

        # Create product category, brand, tag, bike
        self.category = BikeCategoryModel.objects.create(category_name='Mountain')
        self.brand = BikeBrandModel.objects.create(brand_name='Trek')
        self.tag = SpecialTagModel.objects.create(tag_name='Featured')
        self.color = ColorModel.objects.create(color_name='Red', color_code='#FF0000')
        self.size = SizeModel.objects.create(size='M')

        self.bike = BikeModel.objects.create(
            name='Trek Marlin 7',
            price=Decimal('50000.00'),
            category=self.category,
            brand=self.brand,
            special_tag=self.tag,
            stock=10,
            is_available=True,
            is_out_of_stock=False
        )
        self.bike_color = BikeColorsModel.objects.create(bike=self.bike, color=self.color)

        # Setup cart
        self.cart = UserCartModel.objects.create(user=self.user)
        self.cart_item = UserCartItemsModelBike.objects.create(
            user_cart=self.cart,
            bike=self.bike,
            color=self.bike_color,
            size=self.size,
            quantity=2
        )

    @patch('Application.OrderServices.order_views.get_razorpay_client')
    def test_razorpay_initiate_checkout_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.order.create.return_value = {
            'id': 'order_rzp_123456',
            'amount': 10000000,
            'currency': 'INR',
            'receipt': 'test_receipt'
        }
        mock_get_client.return_value = mock_client

        response = self.client.post(
            '/api/order/razorpay/create-order/',
            {'address_id': str(self.address.unique_id)},
            format='json',
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('order_id', response.data)
        self.assertEqual(response.data['razorpay_order_id'], 'order_rzp_123456')
        self.assertEqual(response.data['amount'], 10000000)

        # Verify DB order
        db_order = UserOrdersModel.objects.get(unique_id=response.data['order_id'])
        self.assertEqual(db_order.user, self.user)
        self.assertEqual(db_order.payment_gateway, 'razorpay')
        self.assertEqual(db_order.razorpay_order_id, 'order_rzp_123456')
        self.assertEqual(db_order.status, 'Pending')
        self.assertFalse(db_order.payment_status)
        self.assertEqual(db_order.bike_orders.count(), 1)

    @patch('Application.OrderServices.order_views.get_razorpay_client')
    def test_razorpay_create_order_empty_cart(self, mock_get_client):
        self.cart_item.delete()

        response = self.client.post(
            '/api/order/razorpay/create-order/',
            {'address_id': str(self.address.unique_id)},
            format='json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    @patch('Application.OrderServices.order_utils.order_confirmation_email')
    @patch('Application.OrderServices.order_views.get_razorpay_client')
    def test_razorpay_verify_order_payment_success(self, mock_get_client, mock_email):
        mock_client = MagicMock()
        mock_client.utility.verify_payment_signature.return_value = True
        mock_get_client.return_value = mock_client

        # Create an existing order
        order = UserOrdersModel.objects.create(
            user=self.user,
            user_address=self.address,
            total_amount=Decimal('100000.00'),
            total_items=2,
            status='Pending',
            payment_gateway='razorpay',
            razorpay_order_id='order_rzp_test_999'
        )
        BikeOrderItems.objects.create(
            order=order,
            bike=self.bike,
            color=self.bike_color,
            size=self.size,
            quantity=2,
            price=self.bike.price,
            subtotal=self.bike.price * 2
        )

        initial_stock = self.bike.stock

        payload = {
            'razorpay_order_id': 'order_rzp_test_999',
            'razorpay_payment_id': 'pay_rzp_test_888',
            'razorpay_signature': 'test_signature_valid'
        }

        response = self.client.post(
            '/api/order/razorpay/verify-order/',
            payload,
            format='json',
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')

        order.refresh_from_db()
        self.assertTrue(order.payment_status)
        self.assertEqual(order.status, 'Processing')
        self.assertEqual(order.razorpay_payment_id, 'pay_rzp_test_888')

        # Stock deducted
        self.bike.refresh_from_db()
        self.assertEqual(self.bike.stock, initial_stock - 2)

        # Email sent
        mock_email.assert_called_once()

    @patch('Application.OrderServices.order_utils.order_cancellation_email')
    @patch('Application.OrderServices.order_views.get_razorpay_client')
    def test_razorpay_verify_order_payment_failure(self, mock_get_client, mock_cancel_email):
        mock_client = MagicMock()
        mock_client.utility.verify_payment_signature.side_effect = SignatureVerificationError('Invalid Signature')
        mock_get_client.return_value = mock_client

        order = UserOrdersModel.objects.create(
            user=self.user,
            user_address=self.address,
            total_amount=Decimal('100000.00'),
            total_items=2,
            status='Pending',
            payment_gateway='razorpay',
            razorpay_order_id='order_rzp_fail_111'
        )

        payload = {
            'razorpay_order_id': 'order_rzp_fail_111',
            'razorpay_payment_id': 'pay_rzp_fail_222',
            'razorpay_signature': 'bad_sig'
        }

        response = self.client.post(
            '/api/order/razorpay/verify-order/',
            payload,
            format='json',
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Failed')
        self.assertFalse(order.payment_status)
        self.assertFalse(bool(order.invoice))  # No invoice generated
        mock_cancel_email.assert_called_once()

    @patch('Application.OrderServices.order_utils.order_confirmation_email')
    @patch('Application.OrderServices.order_views.get_razorpay_client')
    def test_razorpay_webhook_order_paid(self, mock_get_client, mock_email):
        mock_client = MagicMock()
        mock_client.utility.verify_webhook_signature.return_value = True
        mock_get_client.return_value = mock_client

        order = UserOrdersModel.objects.create(
            user=self.user,
            user_address=self.address,
            total_amount=Decimal('100000.00'),
            total_items=2,
            status='Pending',
            payment_gateway='razorpay',
            razorpay_order_id='order_rzp_wh_111'
        )
        BikeOrderItems.objects.create(
            order=order,
            bike=self.bike,
            color=self.bike_color,
            size=self.size,
            quantity=1,
            price=self.bike.price,
            subtotal=self.bike.price
        )

        initial_stock = self.bike.stock

        webhook_payload = {
            'event': 'order.paid',
            'payload': {
                'order': {
                    'entity': {
                        'id': 'order_rzp_wh_111',
                        'receipt': str(order.unique_id)
                    }
                },
                'payment': {
                    'entity': {
                        'id': 'pay_rzp_wh_222',
                        'order_id': 'order_rzp_wh_111'
                    }
                }
            }
        }

        body = json.dumps(webhook_payload)
        response = self.client.post(
            '/api/order/razorpay/webhook/',
            body,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='valid_signature'
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertTrue(order.payment_status)
        self.assertEqual(order.status, 'Processing')
        self.assertEqual(order.razorpay_payment_id, 'pay_rzp_wh_222')

        self.bike.refresh_from_db()
        self.assertEqual(self.bike.stock, initial_stock - 1)
        mock_email.assert_called_once()

    @patch('Application.OrderServices.order_views.get_razorpay_client')
    def test_create_order_via_main_endpoint_routing(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.order.create.return_value = {
            'id': 'order_rzp_routed_123',
            'amount': 10000000,
            'currency': 'INR',
            'receipt': 'test_receipt'
        }
        mock_get_client.return_value = mock_client

        response = self.client.post(
            '/api/order/create-order/',
            {
                'address_id': str(self.address.unique_id),
                'payment_gateway': 'razorpay'
            },
            format='json',
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['razorpay_order_id'], 'order_rzp_routed_123')

    @patch('Application.OrderServices.order_utils.order_cancellation_email')
    @patch('Application.OrderServices.order_views.get_razorpay_client')
    def test_webhook_payment_failed(self, mock_get_client, mock_cancel_email):
        mock_client = MagicMock()
        mock_client.utility.verify_webhook_signature.return_value = True
        mock_get_client.return_value = mock_client

        order = UserOrdersModel.objects.create(
            user=self.user,
            user_address=self.address,
            total_amount=Decimal('50000.00'),
            total_items=1,
            status='Pending',
            payment_gateway='razorpay',
            razorpay_order_id='order_rzp_fail_wh'
        )

        webhook_payload = {
            'event': 'payment.failed',
            'payload': {
                'order': {
                    'entity': {
                        'id': 'order_rzp_fail_wh',
                        'receipt': str(order.unique_id)
                    }
                },
                'payment': {
                    'entity': {
                        'id': 'pay_failed_123',
                        'order_id': 'order_rzp_fail_wh'
                    }
                }
            }
        }

        response = self.client.post(
            '/api/order/razorpay/webhook/',
            json.dumps(webhook_payload),
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='valid_sig'
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Failed')
        self.assertFalse(order.payment_status)
        self.assertFalse(bool(order.invoice))  # No invoice
        mock_cancel_email.assert_called_once()

    @patch('Application.OrderServices.order_utils.order_cancellation_email')
    @patch('Application.OrderServices.order_utils.order_confirmation_email')
    def test_razorpay_cancel_order_endpoint(self, mock_confirm_email, mock_cancel_email):
        order = UserOrdersModel.objects.create(
            user=self.user,
            user_address=self.address,
            total_amount=Decimal('50000.00'),
            total_items=1,
            status='Pending',
            payment_gateway='razorpay',
            razorpay_order_id='order_rzp_to_cancel'
        )

        response = self.client.post(
            '/api/order/razorpay/cancel-order/',
            {
                'order_id': str(order.unique_id),
                'reason': 'Customer dismissed payment modal'
            },
            format='json',
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'cancelled')
        self.assertEqual(response.data['order_status'], 'Cancelled')

        order.refresh_from_db()
        self.assertEqual(order.status, 'Cancelled')
        self.assertFalse(order.payment_status)
        self.assertFalse(bool(order.invoice))  # NO invoice generated or attached

        mock_cancel_email.assert_called_once()
        mock_confirm_email.assert_not_called()

    def test_cannot_cancel_already_paid_order(self):
        order = UserOrdersModel.objects.create(
            user=self.user,
            user_address=self.address,
            total_amount=Decimal('50000.00'),
            total_items=1,
            status='Processing',
            payment_status=True,
            payment_gateway='razorpay',
            razorpay_order_id='order_rzp_already_paid'
        )

        response = self.client.post(
            '/api/order/razorpay/cancel-order/',
            {
                'order_id': str(order.unique_id),
                'reason': 'Try to cancel paid order'
            },
            format='json',
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Processing')
        self.assertTrue(order.payment_status)

    def test_product_detail_page_numeric_id_and_uuid(self):
        # 1. Test fetching with integer PK (e.g. "9")
        response_pk = self.client.get(
            f'/api/product/product-detail-page/bike/{self.bike.id}/'
        )
        self.assertEqual(response_pk.status_code, 200)
        self.assertEqual(response_pk.data['name'], self.bike.name)

        # 2. Test fetching with UUID string
        response_uuid = self.client.get(
            f'/api/product/product-detail-page/bike/{self.bike.unique_id}/'
        )
        self.assertEqual(response_uuid.status_code, 200)
        self.assertEqual(response_uuid.data['name'], self.bike.name)

        # 3. Test non-existent product returns 404 instead of 500 ValidationError
        response_404 = self.client.get(
            '/api/product/product-detail-page/bike/999999/'
        )
        self.assertEqual(response_404.status_code, 404)

    def test_duplicate_api_prefix_fallback(self):
        # Test /api/api/order/user-orders/ does not 404
        response = self.client.get(
            '/api/api/order/user-orders/',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)

