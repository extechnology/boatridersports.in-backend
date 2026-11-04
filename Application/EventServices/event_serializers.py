from rest_framework import serializers
from .event_models import Event, EventRegistration


class EventPublicSerializer(serializers.ModelSerializer):
    categoryLabel = serializers.CharField(source='category_label', read_only=True)
    googleMapsUrl = serializers.CharField(source='google_maps_url', read_only=True)
    isFree = serializers.BooleanField(source='is_free', read_only=True)
    maxSpots = serializers.IntegerField(source='max_spots', read_only=True)
    filledSpots = serializers.IntegerField(source='filled_spots', read_only=True)
    spotsLeft = serializers.IntegerField(source='spots_left', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'slug',
            'category',
            'categoryLabel',
            'category_label',
            'tag',
            'date',
            'time',
            'location',
            'googleMapsUrl',
            'google_maps_url',
            'distance',
            'difficulty',
            'fee',
            'isFree',
            'is_free',
            'maxSpots',
            'max_spots',
            'filledSpots',
            'filled_spots',
            'spotsLeft',
            'spots_left',
            'image',
            'description',
            'highlights',
            'schedule',
            'status',
            'is_published',
            'created_at',
            'updated_at',
        ]


class EventRegistrationSerializer(serializers.ModelSerializer):
    registrationId = serializers.CharField(source='id', read_only=True)
    registrationNumber = serializers.CharField(source='registration_number', read_only=True)
    eventId = serializers.CharField(source='event.id', read_only=True)
    eventTitle = serializers.CharField(source='event.title', read_only=True)
    fullName = serializers.CharField(source='full_name', read_only=True)
    bikeType = serializers.CharField(source='bike_type', read_only=True)
    experienceLevel = serializers.CharField(source='experience_level', read_only=True)
    emergencyContact = serializers.CharField(source='emergency_contact', read_only=True)
    paymentStatus = serializers.CharField(source='payment_status', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id',
            'registrationId',
            'registration_number',
            'registrationNumber',
            'event',
            'eventId',
            'eventTitle',
            'full_name',
            'fullName',
            'phone',
            'email',
            'participants',
            'bike_type',
            'bikeType',
            'experience_level',
            'experienceLevel',
            'emergency_contact',
            'emergencyContact',
            'notes',
            'agreed_to_terms',
            'status',
            'payment_status',
            'paymentStatus',
            'created_at',
            'createdAt',
        ]

