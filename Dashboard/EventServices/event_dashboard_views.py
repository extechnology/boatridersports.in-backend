import csv
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404

from Application.permissions import IsSuperUserAuthenticated
from Application.EventServices.event_models import Event, EventRegistration
from .event_dashboard_serializers import (
    EventDashboardListSerializer,
    EventDashboardDetailSerializer,
    EventRegistrationDashboardSerializer
)
from Dashboard.pagination import DashboardPagination


def generate_registrations_csv(registrations_qs, filename="all_event_registrations.csv"):
    """
    Helper to generate UTF-8 BOM Excel-compatible CSV for event registrations.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')  # UTF-8 BOM for Microsoft Excel

    writer = csv.writer(response)
    writer.writerow([
        'Registration ID',
        'Ticket Code',
        'Registration Date',
        'Event ID',
        'Event Title',
        'Event Category',
        'Event Date',
        'Event Time',
        'Event Location',
        'Full Name',
        'Phone',
        'Email',
        'Riders Count',
        'Bike Type',
        'Experience Level',
        'Emergency Contact',
        'Special Notes',
        'Status',
        'Payment Status'
    ])

    for reg in registrations_qs.select_related('event'):
        ev = reg.event
        reg_date = reg.created_at.strftime('%Y-%m-%d %H:%M') if reg.created_at else 'N/A'
        writer.writerow([
            str(reg.id),
            reg.registration_number,
            reg_date,
            ev.id if ev else 'N/A',
            ev.title if ev else 'N/A',
            getattr(ev, 'category_label', '') or getattr(ev, 'category', '') if ev else 'N/A',
            ev.date if ev else 'N/A',
            ev.time if ev else 'N/A',
            ev.location if ev else 'N/A',
            reg.full_name,
            reg.phone,
            reg.email,
            reg.participants,
            reg.bike_type,
            reg.experience_level,
            reg.emergency_contact,
            reg.notes,
            reg.status.capitalize() if reg.status else '',
            reg.payment_status,
        ])

    return response


def filter_registrations_queryset(request):
    """
    Helper to filter EventRegistration queryset across query parameters.
    """
    event_id = request.GET.get('event_id', '').strip()
    category = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip().lower()
    payment_status = request.GET.get('payment_status', '').strip().lower()
    search_query = request.GET.get('search', '').strip()
    time_filter = request.GET.get('filter', '').strip().lower()
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()

    qs = EventRegistration.objects.select_related('event', 'user').all()

    if event_id and event_id.lower() != 'all':
        qs = qs.filter(Q(event__id=event_id) | Q(event__slug=event_id))

    if category and category.lower() != 'all':
        qs = qs.filter(
            Q(event__category__iexact=category) |
            Q(event__category_label__icontains=category)
        )

    if status_filter and status_filter != 'all':
        qs = qs.filter(status__iexact=status_filter)

    if payment_status and payment_status != 'all':
        qs = qs.filter(payment_status__iexact=payment_status)

    if search_query:
        qs = qs.filter(
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(registration_number__icontains=search_query) |
            Q(emergency_contact__icontains=search_query) |
            Q(event__title__icontains=search_query) |
            Q(event__location__icontains=search_query) |
            Q(event__id__icontains=search_query)
        )

    now_date = timezone.now()
    if time_filter == 'today':
        start_date = now_date.replace(hour=0, minute=0, second=0, microsecond=0)
        qs = qs.filter(created_at__gte=start_date)
    elif time_filter == 'this_week':
        start_date = (now_date - timedelta(days=now_date.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        qs = qs.filter(created_at__gte=start_date)
    elif time_filter == 'this_month':
        start_date = now_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        qs = qs.filter(created_at__gte=start_date)
    elif time_filter == 'this_year':
        start_date = now_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        qs = qs.filter(created_at__gte=start_date)

    if start_date_str:
        try:
            s_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            s_date = timezone.make_aware(s_date) if timezone.is_naive(s_date) else s_date
            qs = qs.filter(created_at__gte=s_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            e_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            e_date = timezone.make_aware(e_date) if timezone.is_naive(e_date) else e_date
            qs = qs.filter(created_at__lte=e_date)
        except ValueError:
            pass

    return qs.order_by('-created_at')


class DashboardEventListCreateView(APIView):
    """
    GET  /api/admin/events/ or /api/dashboard/events/ - List all events with metrics.
    POST /api/admin/events/ or /api/dashboard/events/ - Create a new event.
    """
    permission_classes = [IsSuperUserAuthenticated]

    def get(self, request):
        category = request.GET.get('category', '').strip()
        status_param = request.GET.get('status', '').strip().lower()
        search_query = request.GET.get('search', '').strip()

        events_qs = Event.objects.all().prefetch_related('registrations')

        if category and category.lower() != 'all':
            events_qs = events_qs.filter(
                Q(category__iexact=category) | Q(category_label__icontains=category)
            )

        if status_param and status_param != 'all':
            events_qs = events_qs.filter(status__iexact=status_param)

        if search_query:
            events_qs = events_qs.filter(
                Q(title__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(id__icontains=search_query)
            )

        events_qs = events_qs.order_by('-created_at')

        # Pagination support if requested or standard
        paginate = request.GET.get('paginate', 'true').lower()
        if paginate == 'false' or paginate == '0':
            serializer = EventDashboardListSerializer(events_qs, many=True)
            return Response({
                "success": True,
                "count": len(serializer.data),
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        paginator = DashboardPagination()
        paginated_qs = paginator.paginate_queryset(events_qs, request)
        serializer = EventDashboardListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = EventDashboardDetailSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save()
            return Response({
                "success": True,
                "message": "Event created successfully.",
                "data": EventDashboardDetailSerializer(event).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DashboardEventDetailView(APIView):
    """
    GET    /api/admin/events/<id>/ - Get single event record.
    PUT    /api/admin/events/<id>/ - Full update of event.
    PATCH  /api/admin/events/<id>/ - Partial update of event.
    DELETE /api/admin/events/<id>/ - Delete or archive event.
    """
    permission_classes = [IsSuperUserAuthenticated]

    def get_object(self, id_or_slug):
        return Event.objects.filter(Q(id=id_or_slug) | Q(slug=id_or_slug)).first()

    def get(self, request, id):
        event = self.get_object(id)
        if not event:
            return Response({"success": False, "message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EventDashboardDetailSerializer(event)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, id):
        event = self.get_object(id)
        if not event:
            return Response({"success": False, "message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EventDashboardDetailSerializer(event, data=request.data)
        if serializer.is_valid():
            updated = serializer.save()
            return Response({
                "success": True,
                "message": "Event updated successfully.",
                "data": EventDashboardDetailSerializer(updated).data
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        event = self.get_object(id)
        if not event:
            return Response({"success": False, "message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EventDashboardDetailSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response({
                "success": True,
                "message": "Event updated successfully.",
                "data": EventDashboardDetailSerializer(updated).data
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        event = self.get_object(id)
        if not event:
            return Response({"success": False, "message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        # Soft delete / archive if requested
        if request.GET.get('archive', '').lower() in ['true', '1']:
            event.is_published = False
            event.status = 'cancelled'
            event.save(update_fields=['is_published', 'status', 'updated_at'])
            return Response({
                "success": True,
                "message": "Event archived and unpublished successfully."
            }, status=status.HTTP_200_OK)

        event.delete()
        return Response({
            "success": True,
            "message": "Event deleted successfully."
        }, status=status.HTTP_200_OK)


class DashboardEventRegistrationsView(APIView):
    """
    GET /api/admin/events/<id>/registrations/ - Get all registrations for an event.
    Supports filtering by status and search query.
    """
    permission_classes = [IsSuperUserAuthenticated]

    def get(self, request, id):
        event = Event.objects.filter(Q(id=id) | Q(slug=id)).first()
        if not event:
            return Response({"success": False, "message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        status_filter = request.GET.get('status', '').strip().lower()
        search_query = request.GET.get('search', '').strip()

        registrations_qs = event.registrations.all()

        if status_filter and status_filter != 'all':
            registrations_qs = registrations_qs.filter(status__iexact=status_filter)

        if search_query:
            registrations_qs = registrations_qs.filter(
                Q(full_name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(registration_number__icontains=search_query) |
                Q(emergency_contact__icontains=search_query)
            )

        registrations_qs = registrations_qs.order_by('-created_at')

        paginate = request.GET.get('paginate', 'false').lower()
        if paginate in ['true', '1']:
            paginator = DashboardPagination()
            paginated_qs = paginator.paginate_queryset(registrations_qs, request)
            serializer = EventRegistrationDashboardSerializer(paginated_qs, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = EventRegistrationDashboardSerializer(registrations_qs, many=True)
        return Response({
            "success": True,
            "eventId": event.id,
            "eventTitle": event.title,
            "totalRegistrations": len(serializer.data),
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class DashboardRegistrationStatusUpdateView(APIView):
    """
    PATCH /api/admin/events/registrations/<id>/status/ - Update registration status.
    Supported statuses: 'confirmed', 'attended', 'cancelled', 'waitlist'.
    Safely adjusts event filled_spots if cancelling or un-cancelling.
    """
    permission_classes = [IsSuperUserAuthenticated]

    def patch(self, request, id):
        new_status = request.data.get('status', '').strip().lower()
        allowed_statuses = ['confirmed', 'attended', 'cancelled', 'waitlist']
        if not new_status or new_status not in allowed_statuses:
            return Response({
                "success": False,
                "message": f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        registration = EventRegistration.objects.filter(id=id).select_related('event').first()
        if not registration:
            return Response({"success": False, "message": "Registration not found."}, status=status.HTTP_404_NOT_FOUND)

        old_status = registration.status
        if old_status == new_status:
            return Response({
                "success": True,
                "message": f"Registration status is already {new_status}.",
                "data": EventRegistrationDashboardSerializer(registration).data
            }, status=status.HTTP_200_OK)

        with transaction.atomic():
            event_locked = Event.objects.select_for_update().get(id=registration.event.id)

            # If moving to cancelled from an active spot
            if new_status == 'cancelled' and old_status in ['confirmed', 'attended']:
                Event.objects.filter(id=event_locked.id).update(
                    filled_spots=F('filled_spots') - registration.participants
                )
            # If moving back to confirmed from cancelled
            elif old_status == 'cancelled' and new_status in ['confirmed', 'attended']:
                Event.objects.filter(id=event_locked.id).update(
                    filled_spots=F('filled_spots') + registration.participants
                )

            registration.status = new_status
            registration.save(update_fields=['status', 'updated_at'])

        return Response({
            "success": True,
            "message": f"Registration status updated to '{new_status}' successfully.",
            "data": EventRegistrationDashboardSerializer(registration).data
        }, status=status.HTTP_200_OK)


class DashboardEventExportCSVView(APIView):
    """
    GET /api/admin/events/<id>/export-csv/
    GET /api/dashboard/events/<id>/export-excel/
    Downloads full Excel-compatible CSV of registered riders for ride marshals and organizers.
    """
    permission_classes = [IsSuperUserAuthenticated]

    def get(self, request, id):
        event = Event.objects.filter(Q(id=id) | Q(slug=id)).first()
        if not event:
            return Response({"success": False, "message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        registrations = event.registrations.all().order_by('-created_at')
        filename = f"event_{event.slug or event.id}_attendees.csv"
        return generate_registrations_csv(registrations, filename=filename)


class DashboardTotalEventRegistrationsView(APIView):
    """
    GET /api/dashboard/events/registrations/
    GET /api/dashboard/events/registrations/all/
    GET /api/dashboard/events/total-registrations/
    
    Lists event registrations across ALL events with filtering, search, metrics,
    and direct Excel export support (?export=excel or ?export=csv).
    """
    permission_classes = [IsSuperUserAuthenticated]

    def get(self, request):
        qs = filter_registrations_queryset(request)

        # Excel / CSV Export if requested via query param
        export_format = request.GET.get('export', '').strip().lower()
        if export_format in ['excel', 'csv']:
            event_id = request.GET.get('event_id', '').strip()
            filename = f"event_{event_id}_applications.csv" if event_id and event_id.lower() != 'all' else "all_event_applications.csv"
            return generate_registrations_csv(qs, filename=filename)

        # Summary KPIs across filtered queryset
        total_applications = qs.count()
        total_riders = qs.aggregate(total=Sum('participants'))['total'] or 0
        confirmed_riders = qs.filter(status='confirmed').aggregate(total=Sum('participants'))['total'] or 0
        attended_riders = qs.filter(status='attended').aggregate(total=Sum('participants'))['total'] or 0
        cancelled_riders = qs.filter(status='cancelled').aggregate(total=Sum('participants'))['total'] or 0
        waitlist_riders = qs.filter(status='waitlist').aggregate(total=Sum('participants'))['total'] or 0

        summary = {
            "totalApplications": total_applications,
            "totalRiders": total_riders,
            "confirmedRiders": confirmed_riders,
            "attendedRiders": attended_riders,
            "cancelledRiders": cancelled_riders,
            "waitlistRiders": waitlist_riders,
        }

        paginate = request.GET.get('paginate', 'true').lower()
        if paginate in ['false', '0']:
            serializer = EventRegistrationDashboardSerializer(qs, many=True)
            return Response({
                "success": True,
                "summary": summary,
                "count": len(serializer.data),
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        paginator = DashboardPagination()
        paginated_qs = paginator.paginate_queryset(qs, request)
        serializer = EventRegistrationDashboardSerializer(paginated_qs, many=True)
        response = paginator.get_paginated_response(serializer.data)
        response.data['summary'] = summary
        return response


class DashboardAllRegistrationsExcelExportView(APIView):
    """
    GET /api/dashboard/events/export-excel/
    GET /api/admin/events/export-excel/
    Direct dedicated endpoint to download all filtered registrations in Excel-compatible CSV format.
    """
    permission_classes = [IsSuperUserAuthenticated]

    def get(self, request):
        qs = filter_registrations_queryset(request)
        event_id = request.GET.get('event_id', '').strip()
        filename = f"event_{event_id}_applications.csv" if event_id and event_id.lower() != 'all' else "all_event_applications.csv"
        return generate_registrations_csv(qs, filename=filename)


