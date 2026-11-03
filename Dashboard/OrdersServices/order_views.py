from rest_framework.decorators import permission_classes
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
import calendar

from Application.permissions import IsSuperUserAuthenticated
from Application.OrderServices.order_models import UserOrdersModel
from .order_serializers import UserOrdersModelSerializerDashboard
from .order_serializers import OrderStatusUpdateSerializer
from .order_utils import order_updation_mail
from ..pagination import DashboardPagination


class TotalOrdersAPIView(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    pagination_class = DashboardPagination

    def get(self, request):
        filter_type = request.GET.get('filter', 'all_time')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        month_str = request.GET.get('month')
        year_str = request.GET.get('year')
        search_query = request.GET.get('search', '').strip()

        now_date = timezone.now()
        start_date = None
        end_date = now_date

        if filter_type == 'today':
            start_date = now_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_type == 'this_week':
            start_date = (now_date - timedelta(days=now_date.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif filter_type == 'this_month':
            start_date = now_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif filter_type == 'this_year':
            start_date = now_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif filter_type == 'custom_month' and month_str and year_str:
            try:
                m, y = int(month_str), int(year_str)
                last_day = calendar.monthrange(y, m)[1]
                start_date = now_date.replace(year=y, month=m, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now_date.replace(year=y, month=m, day=last_day, hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                pass
        elif filter_type == 'custom_year' and year_str:
            try:
                y = int(year_str)
                start_date = now_date.replace(year=y, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now_date.replace(year=y, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                pass
        elif filter_type == 'custom' and start_date_str and end_date_str:
            try:
                parsed_start = datetime.strptime(start_date_str, "%Y-%m-%d")
                parsed_end = datetime.strptime(end_date_str, "%Y-%m-%d")
                start_date = timezone.make_aware(parsed_start) if timezone.is_naive(parsed_start) else parsed_start
                end_date = (timezone.make_aware(parsed_end) if timezone.is_naive(parsed_end) else parsed_end).replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
            except ValueError:
                pass

        try:
            orders_q = UserOrdersModel.objects.all().order_by('-created_at')

            if search_query:
                orders_q = orders_q.filter(
                    Q(unique_id__icontains=search_query) |
                    Q(user__username__icontains=search_query) |
                    Q(user__fullname__icontains=search_query) |
                    Q(user__email__icontains=search_query) |
                    Q(user__phone__icontains=search_query) |
                    Q(user_address__name__icontains=search_query) |
                    Q(user_address__phone_number__icontains=search_query) |
                    Q(user_address__address__icontains=search_query) |
                    Q(user_address__city__icontains=search_query) |
                    Q(user_address__state__icontains=search_query) |
                    Q(user_address__pincode__icontains=search_query) |
                    Q(status__icontains=search_query)
                ).distinct()

            if start_date:
                orders_q = orders_q.filter(created_at__range=[start_date, end_date])

            export_format = request.GET.get('export', '').lower()
            if export_format == 'excel':
                response = HttpResponse(content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
                response.write('\ufeff')  # UTF-8 BOM for Microsoft Excel

                writer = csv.writer(response)
                # Header with customer details and full address fields
                writer.writerow([
                    'Order ID',
                    'Order Date',
                    'Customer Name',
                    'Customer Email',
                    'Customer Phone',
                    'Address Type',
                    'Delivery Address',
                    'City',
                    'State',
                    'Pincode',
                    'Full Address',
                    'Order Status',
                    'Payment Status',
                    'Payment Gateway',
                    'Tracking ID',
                    'Shipped Via',
                    'Order Total',
                    'Product Type',
                    'Product Name',
                    'Category',
                    'Color',
                    'Size',
                    'Price',
                    'Quantity',
                    'Subtotal'
                ])

                for order in orders_q.select_related('user', 'user_address').prefetch_related(
                    'bike_orders__bike__category', 'bike_orders__color__color', 'bike_orders__size',
                    'accessories_orders__accessory__sub_category__category'
                ):
                    order_date = order.created_at.strftime('%Y-%m-%d %H:%M') if getattr(order, 'created_at', None) else 'N/A'

                    addr = getattr(order, 'user_address', None)
                    user = getattr(order, 'user', None)

                    # Customer Name
                    if addr and addr.name:
                        user_name = addr.name
                    elif user:
                        user_name = user.fullname or user.username or 'N/A'
                    else:
                        user_name = 'N/A'

                    # Customer Email
                    user_email = user.email if user and user.email else 'N/A'

                    # Customer Phone
                    if addr and addr.phone_number:
                        user_phone = addr.phone_number
                    elif user and getattr(user, 'phone', None):
                        user_phone = user.phone
                    else:
                        user_phone = 'N/A'

                    # Address fields
                    address_type = addr.address_type if addr and addr.address_type else 'N/A'
                    street_address = addr.address if addr and addr.address else 'N/A'
                    city = addr.city if addr and addr.city else 'N/A'
                    state = addr.state if addr and addr.state else 'N/A'
                    pincode = addr.pincode if addr and addr.pincode else 'N/A'

                    if addr:
                        parts = [p for p in [addr.address, addr.city, addr.state] if p]
                        full_address = ", ".join(parts)
                        if addr.pincode:
                            full_address = f"{full_address} - {addr.pincode}" if full_address else addr.pincode
                    else:
                        full_address = 'N/A'

                    order_status = order.status
                    payment_status = 'Paid' if order.payment_status else 'Unpaid'
                    payment_gateway = order.payment_gateway or 'N/A'
                    tracking_id = order.tracking_id or 'N/A'
                    shipped_via = order.shipped_via or 'N/A'
                    order_total = str(order.total_amount)

                    base_row = [
                        order.unique_id,
                        order_date,
                        user_name,
                        user_email,
                        user_phone,
                        address_type,
                        street_address,
                        city,
                        state,
                        pincode,
                        full_address,
                        order_status,
                        payment_status,
                        payment_gateway,
                        tracking_id,
                        shipped_via,
                        order_total
                    ]

                    # Bikes
                    for b in order.bike_orders.all():
                        p_type = 'Bike'
                        p_name = b.bike.name if getattr(b, 'bike', None) else 'Unknown Bike'
                        cat = b.bike.category.category_name if getattr(b, 'bike', None) and getattr(b.bike, 'category', None) else 'N/A'
                        color = b.color.color.color_name if getattr(b, 'color', None) and getattr(b.color, 'color', None) else 'N/A'
                        size = b.size.size if getattr(b, 'size', None) else 'N/A'
                        price = str(b.price)
                        qty = str(b.quantity)
                        subtotal = str(b.subtotal)

                        writer.writerow(base_row + [p_type, p_name, cat, color, size, price, qty, subtotal])

                    # Accessories
                    for a in order.accessories_orders.all():
                        p_type = 'Accessory'
                        p_name = a.accessory.name if getattr(a, 'accessory', None) else 'Unknown Accessory'
                        cat = a.accessory.sub_category.category.name if (
                            getattr(a, 'accessory', None) and
                            getattr(a.accessory, 'sub_category', None) and
                            getattr(a.accessory.sub_category, 'category', None)
                        ) else 'N/A'
                        color = 'N/A'
                        size = 'N/A'
                        price = str(a.price)
                        qty = str(a.quantity)
                        subtotal = str(a.subtotal)

                        writer.writerow(base_row + [p_type, p_name, cat, color, size, price, qty, subtotal])

                    # If order has no items for some reason
                    if not order.bike_orders.exists() and not order.accessories_orders.exists():
                        writer.writerow(base_row + ['N/A', 'N/A', 'N/A', 'N/A', 'N/A', '0', '0', '0'])

                return response

            paginator = DashboardPagination()
            orders_q = orders_q.select_related('user', 'user_address').prefetch_related(
                'bike_orders__bike__category', 'bike_orders__color__color', 'bike_orders__size',
                'accessories_orders__accessory__sub_category__category'
            )
            paginated_qs = paginator.paginate_queryset(orders_q, request)

            serializer = UserOrdersModelSerializerDashboard(paginated_qs, many=True, context={"request": request})

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderStatusUpdate(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    serializer_class = OrderStatusUpdateSerializer

    def patch(self, request, order_id):
        deliverd_at = request.data.get('deliverd_at')
        tracking_id = request.data.get('tracking_id')
        shipped_via = request.data.get('shipped_via')
        order_status = request.data.get('status')
        if not order_id:
            return Response({"error": "Unique ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = UserOrdersModel.objects.get(unique_id=order_id)
            if deliverd_at:
                order.deliverd_at = deliverd_at
            if tracking_id:
                order.tracking_id = tracking_id
            if shipped_via:
                order.shipped_via = shipped_via
            if order_status:
                order.status = order_status
            order.save()

            order_updation_mail(order)

            return Response({"message": "Order status updated successfully"}, status=status.HTTP_200_OK)
        except UserOrdersModel.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
