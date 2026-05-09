from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import timedelta, datetime
import calendar

from Application.ProductServices.product_models import (
    BikeModel,
    AccessoriesModel,
)

from Application.AuthenticationServices.auth_utils import (
    get_user_from_request
)

from Application.AuthenticationServices.auth_models import (
    User
)

from Application.OrderServices.order_models import (
    UserOrdersModel,
    BikeOrderItems,
    AccessoriesOrderItems
)

from Application.ProfileServices.profile_models import (
    UserAddress
)

from Application.permissions import IsSuperUserAuthenticated



class DashboardStatsView(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    
    def get(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        filter_type = request.GET.get('filter', 'all_time')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        month_str = request.GET.get('month')
        year_str = request.GET.get('year')

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
            bike_orders_q = BikeOrderItems.objects.filter(order__payment_status=True)
            acc_orders_q = AccessoriesOrderItems.objects.filter(order__payment_status=True)
            products_bike_q = BikeModel.objects.all()
            products_acc_q = AccessoriesModel.objects.all()
            users_q = User.objects.all()
            orders_q = UserOrdersModel.objects.filter(payment_status=True)

            if start_date:
                bike_orders_q = bike_orders_q.filter(created_at__range=[start_date, end_date])
                acc_orders_q = acc_orders_q.filter(created_at__range=[start_date, end_date])
                products_bike_q = products_bike_q.filter(created__range=[start_date, end_date])
                products_acc_q = products_acc_q.filter(created__range=[start_date, end_date])
                users_q = users_q.filter(date_joined__range=[start_date, end_date])
                orders_q = orders_q.filter(created_at__range=[start_date, end_date])

            total_orders = bike_orders_q.count() + acc_orders_q.count()
            total_products = products_bike_q.count() + products_acc_q.count()
            total_users = users_q.count()
            total_revenue = orders_q.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            # Generate Graph Data
            actual_start = start_date
            actual_end = end_date

            if filter_type == 'all_time' or not actual_start:
                actual_start = now_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                actual_end = now_date.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            elif filter_type == 'this_year':
                actual_end = actual_start.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            elif filter_type == 'this_month':
                last_day = calendar.monthrange(actual_start.year, actual_start.month)[1]
                actual_end = actual_start.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
            elif filter_type == 'this_week':
                actual_end = (actual_start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)

            duration = (actual_end - actual_start).days
            if duration <= 31:
                trunc_func = TruncDay('created_at')
                date_format = '%b %d'
                key_format = '%Y-%m-%d'
            else:
                trunc_func = TruncMonth('created_at')
                date_format = '%b'
                key_format = '%Y-%m'

            current_date = actual_start
            date_items = []
            
            while current_date.date() <= actual_end.date():
                key = current_date.strftime(key_format)
                label = current_date.strftime(date_format)
                if not any(item['key'] == key for item in date_items):
                    date_items.append({'key': key, 'label': label})
                
                if duration <= 31:
                    current_date += timedelta(days=1)
                else:
                    current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

            orders_graph_q = orders_q.annotate(
                date=trunc_func
            ).values('date').annotate(
                orders=Count('id'),
                revenue=Sum('total_amount')
            ).order_by('date')

            graph_data = {}
            for entry in orders_graph_q:
                if entry['date']:
                    key = entry['date'].strftime(key_format)
                    graph_data[key] = {
                        "revenue": entry['revenue'] or 0,
                        "orders": entry['orders'] or 0
                    }

            revenue_overview = []
            orders_per_month = []

            for item in date_items:
                key = item['key']
                label = item['label']
                data = graph_data.get(key, {"revenue": 0, "orders": 0})
                
                revenue_overview.append({
                    "name": label,
                    "revenue": data["revenue"]
                })
                orders_per_month.append({
                    "name": label,
                    "orders": data["orders"]
                })

            return Response({
                "total_orders": total_orders,
                "total_products": total_products,
                "total_users": total_users,
                "total_revenue": total_revenue,
                "revenue_overview": revenue_overview,
                "orders_per_month": orders_per_month
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class RecentOrdersView(APIView):
    permission_classes = [IsSuperUserAuthenticated]
    
    def get(self, request):
        try:
            bike_orders = BikeOrderItems.objects.select_related('order', 'order__user_address', 'bike').all().order_by("-created_at")[:6]
            accessory_orders = AccessoriesOrderItems.objects.select_related('order', 'order__user_address', 'accessory').all().order_by("-created_at")[:6]
            
            combined = []
            for b in bike_orders:
                combined.append({
                    "id": b.id,
                    "order_id": b.order.unique_id if b.order else None,
                    "customer": b.order.user_address.name if b.order and b.order.user_address else "Unknown",
                    "product": b.bike.name if b.bike else "Unknown Bike",
                    "amount": b.subtotal,
                    "status": b.order.status if b.order else "Unknown",
                    "date": b.created_at
                })
                
            for a in accessory_orders:
                combined.append({
                    "id": a.id,
                    "order_id": a.order.unique_id if a.order else None,
                    "customer": a.order.user_address.name if a.order and a.order.user_address else "Unknown",
                    "product": a.accessory.name if a.accessory else "Unknown Accessory",
                    "amount": a.subtotal,
                    "status": a.order.status if a.order else "Unknown",
                    "date": a.created_at
                })
                
            # Sort by date descending
            combined.sort(key=lambda x: x['date'], reverse=True)
            
            return Response(combined[:6], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
