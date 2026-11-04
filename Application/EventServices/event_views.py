import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.db.models import F, Q

from .event_models import Event, EventRegistration
from .event_serializers import EventPublicSerializer, EventRegistrationSerializer
from .event_utils import send_event_registration_confirmation
from Application.AuthenticationServices.auth_utils import get_user_from_request


def get_optional_user(request):
    """
    Safely retrieves the authenticated User if a valid JWT or session is present.
    Returns None for guest users without raising an exception.
    """
    try:
        if hasattr(request, 'user') and request.user and getattr(request.user, 'is_authenticated', False):
            return request.user
        return get_user_from_request(request)
    except Exception:
        return None


class EventListView(APIView):
    """
    GET /api/events/
    Fetches list of published events with optional filtering by category, search, and status.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.GET.get('category', '').strip()
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', 'upcoming').strip().lower()

        events_qs = Event.objects.filter(is_published=True)

        # Filter by status if not 'all'
        if status_filter and status_filter != 'all':
            events_qs = events_qs.filter(status__iexact=status_filter)

        # Filter by category
        if category and category.lower() != 'all':
            events_qs = events_qs.filter(
                Q(category__iexact=category) | Q(category_label__icontains=category)
            )

        # Search in title, location, description, or distance
        if search_query:
            events_qs = events_qs.filter(
                Q(title__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(distance__icontains=search_query)
            )

        events_qs = events_qs.order_by('-created_at')
        serializer = EventPublicSerializer(events_qs, many=True)

        return Response({
            "success": True,
            "count": len(serializer.data),
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class EventDetailView(APIView):
    """
    GET /api/events/<id_or_slug>/
    Fetches single event details by its ID or slug.
    """
    permission_classes = [AllowAny]

    def get(self, request, id_or_slug):
        event = Event.objects.filter(
            Q(id=id_or_slug) | Q(slug=id_or_slug)
        ).first()

        if not event:
            return Response({
                "success": False,
                "message": "Event not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # If unpublished, only staff/superuser can view
        if not event.is_published:
            user = get_optional_user(request)
            is_authorized = bool(user and (getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)))
            if not is_authorized:
                return Response({
                    "success": False,
                    "message": "Event is not currently published."
                }, status=status.HTTP_404_NOT_FOUND)

        serializer = EventPublicSerializer(event)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class EventRegistrationView(APIView):
    """
    POST /api/events/register/
    Registers one or more participants for an event directly.
    CRITICAL REQUIREMENT: No payment gateway step is required.
    Directly marks spot as confirmed and returns ticket details.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        event_id = data.get('eventId') or data.get('event_id') or data.get('event')
        full_name = (data.get('fullName') or data.get('full_name') or '').strip()
        phone = (data.get('phone') or '').strip()
        email = (data.get('email') or '').strip()

        try:
            participants = int(data.get('participants', 1))
            if participants < 1:
                participants = 1
        except (ValueError, TypeError):
            participants = 1

        bike_type = (data.get('bikeType') or data.get('bike_type') or 'Road Bike').strip()
        experience_level = (data.get('experienceLevel') or data.get('experience_level') or 'Intermediate').strip()
        emergency_contact = (data.get('emergencyContact') or data.get('emergency_contact') or '').strip()
        notes = (data.get('notes') or '').strip()
        agreed_to_terms = data.get('agreedToTerms', data.get('agreed_to_terms', True))

        # 1. Validate required fields
        if not event_id:
            return Response({"success": False, "message": "Event ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not full_name:
            return Response({"success": False, "message": "Full name is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not phone:
            return Response({"success": False, "message": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({"success": False, "message": "Email address is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Terms agreement check
        if not agreed_to_terms or str(agreed_to_terms).lower() in ['false', '0', 'no']:
            return Response({
                "success": False,
                "message": "You must agree to the safety pledge and event terms."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Format validations
        digits_phone = re.sub(r'\D', '', phone)
        if len(digits_phone) < 10:
            return Response({
                "success": False,
                "message": "Please enter a valid phone number (minimum 10 digits)."
            }, status=status.HTTP_400_BAD_REQUEST)

        if '@' not in email or '.' not in email.split('@')[-1]:
            return Response({
                "success": False,
                "message": "Please enter a valid email address."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 4. Fetch event
        event = Event.objects.filter(
            Q(id=event_id) | Q(slug=event_id),
            is_published=True
        ).first()

        if not event:
            return Response({
                "success": False,
                "message": "Event not found or registration closed."
            }, status=status.HTTP_404_NOT_FOUND)

        if event.status in ['cancelled', 'completed']:
            return Response({
                "success": False,
                "message": f"Registrations are closed because this event is {event.status}."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 5. Check duplicate registration
        existing_reg = EventRegistration.objects.filter(
            event=event,
            status__in=['confirmed', 'attended', 'waitlist']
        ).filter(
            Q(phone=phone) | Q(phone=digits_phone) | Q(email__iexact=email)
        ).first()

        if existing_reg:
            return Response({
                "success": False,
                "message": "You have already registered for this event with this phone number or email."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 6. Check available spots
        available_spots = event.max_spots - event.filled_spots
        if available_spots < participants:
            remaining = max(0, available_spots)
            return Response({
                "success": False,
                "message": f"Only {remaining} spot{'s' if remaining != 1 else ''} remaining for this ride."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 7. Identify logged-in user if available (optional)
        user = get_optional_user(request)

        # 8. Concurrency-safe atomic registration
        try:
            with transaction.atomic():
                # Re-lock event to guarantee capacity
                event_locked = Event.objects.select_for_update().get(id=event.id)
                current_available = event_locked.max_spots - event_locked.filled_spots
                if current_available < participants:
                    remaining = max(0, current_available)
                    return Response({
                        "success": False,
                        "message": f"Only {remaining} spot{'s' if remaining != 1 else ''} remaining for this ride."
                    }, status=status.HTTP_400_BAD_REQUEST)

                registration = EventRegistration.objects.create(
                    event=event_locked,
                    user=user,
                    full_name=full_name,
                    phone=phone,
                    email=email,
                    participants=participants,
                    bike_type=bike_type,
                    experience_level=experience_level,
                    emergency_contact=emergency_contact,
                    notes=notes,
                    agreed_to_terms=True,
                    status='confirmed',
                    payment_status='not_required',
                )

                # Atomically update filled_spots
                Event.objects.filter(id=event_locked.id).update(
                    filled_spots=F('filled_spots') + participants
                )
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Unable to process registration: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 9. Asynchronously/safely trigger confirmation email
        send_event_registration_confirmation(registration)

        # 10. Return confirmation response
        return Response({
            "success": True,
            "message": "Registration confirmed successfully! Spot reserved.",
            "data": {
                "registrationId": str(registration.id),
                "registrationNumber": registration.registration_number,
                "eventId": event.id,
                "eventTitle": event.title,
                "fullName": registration.full_name,
                "phone": registration.phone,
                "email": registration.email,
                "participants": registration.participants,
                "bikeType": registration.bike_type,
                "experienceLevel": registration.experience_level,
                "status": registration.status,
                "paymentStatus": registration.payment_status,
                "createdAt": registration.created_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)
