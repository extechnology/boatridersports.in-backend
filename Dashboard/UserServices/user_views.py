from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from Application.AuthenticationServices.auth_models import User
from Application.OrderServices.order_models import UserOrdersModel

from .user_serializers import UserSerializerDashboard
from Application.permissions import IsSuperUserAuthenticated
from django.utils import timezone
from datetime import timedelta, datetime
import calendar

from django.db.models import Q
from ..pagination import DashboardPagination

class TotalUsersView(APIView):
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
        
        user_q = User.objects.all().order_by('-date_joined')

        if start_date and end_date:
            user_q = user_q.filter(date_joined__range=(start_date, end_date))

        if search_query:
            user_q = user_q.filter(
                Q(unique_id__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(phone__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
            )

        user_q = user_q.distinct()

        paginator = DashboardPagination()
        paginated_qs = paginator.paginate_queryset(user_q, request)
        serializer = UserSerializerDashboard(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)