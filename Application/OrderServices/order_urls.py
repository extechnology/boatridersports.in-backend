from django.urls import path
from .order_views import (
    UserOrders,
    InitaiteChcekOutAPIview,
    VerifyOrderPayment,
    RazorpayInitiateCheckoutAPIView,
    RazorpayVerifyOrderPayment,
    RazorpayWebhookAPIView,
    RazorpayCancelOrderAPIView,
)

urlpatterns = [
    path('user-orders/', UserOrders.as_view(), name='user-orders'),
    path('create-order/', InitaiteChcekOutAPIview.as_view(), name='user-order-create'),
    path('verify-order/', VerifyOrderPayment.as_view(), name='user-order-verify'),
    path('cancel-order/', RazorpayCancelOrderAPIView.as_view(), name='cancel-order'),

    # Razorpay URLs
    path('razorpay/create-order/', RazorpayInitiateCheckoutAPIView.as_view(), name='razorpay-create-order'),
    path('razorpay/verify-order/', RazorpayVerifyOrderPayment.as_view(), name='razorpay-verify-order'),
    path('razorpay/cancel-order/', RazorpayCancelOrderAPIView.as_view(), name='razorpay-cancel-order'),
    path('razorpay/webhook/', RazorpayWebhookAPIView.as_view(), name='razorpay-webhook'),

    # Direct alias URLs
    path('razorpay-create-order/', RazorpayInitiateCheckoutAPIView.as_view(), name='razorpay-create-order-direct'),
    path('razorpay-verify-order/', RazorpayVerifyOrderPayment.as_view(), name='razorpay-verify-order-direct'),
    path('razorpay-cancel-order/', RazorpayCancelOrderAPIView.as_view(), name='razorpay-cancel-order-direct'),
    path('razorpay-webhook/', RazorpayWebhookAPIView.as_view(), name='razorpay-webhook-direct'),
]
