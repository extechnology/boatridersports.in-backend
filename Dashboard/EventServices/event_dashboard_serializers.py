from rest_framework import serializers
from django.db.models import Sum
from Application.EventServices.event_models import Event, EventRegistration


class EventRegistrationDashboardSerializer(serializers.ModelSerializer):
    event_id = serializers.CharField(source='event.id', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    ticket_code = serializers.CharField(source='registration_number', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id',
            'registration_number',
            'ticket_code',
            'event',
            'event_id',
            'event_title',
            'user',
            'full_name',
            'phone',
            'email',
            'participants',
            'bike_type',
            'experience_level',
            'emergency_contact',
            'notes',
            'agreed_to_terms',
            'status',
            'payment_status',
            'created_at',
            'updated_at',
        ]


class EventDashboardListSerializer(serializers.ModelSerializer):
    spots_left = serializers.IntegerField(read_only=True)
    total_registrations = serializers.SerializerMethodField()
    confirmed_riders = serializers.SerializerMethodField()
    attended_riders = serializers.SerializerMethodField()
    cancelled_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'slug',
            'category',
            'category_label',
            'tag',
            'date',
            'time',
            'location',
            'google_maps_url',
            'distance',
            'difficulty',
            'fee',
            'is_free',
            'max_spots',
            'filled_spots',
            'spots_left',
            'total_registrations',
            'confirmed_riders',
            'attended_riders',
            'cancelled_count',
            'image',
            'description',
            'highlights',
            'schedule',
            'status',
            'is_published',
            'created_at',
            'updated_at',
        ]

    def get_total_registrations(self, obj):
        return obj.registrations.count()

    def get_confirmed_riders(self, obj):
        result = obj.registrations.filter(status='confirmed').aggregate(total=Sum('participants'))['total']
        return result or 0

    def get_attended_riders(self, obj):
        result = obj.registrations.filter(status='attended').aggregate(total=Sum('participants'))['total']
        return result or 0

    def get_cancelled_count(self, obj):
        return obj.registrations.filter(status='cancelled').count()


class EventDashboardDetailSerializer(serializers.ModelSerializer):
    spots_left = serializers.IntegerField(read_only=True)
    id = serializers.CharField(required=False)

    class Meta:
        model = Event
        fields = '__all__'

    def validate_max_spots(self, value):
        if value < 1:
            raise serializers.ValidationError("max_spots must be at least 1.")
        return value

