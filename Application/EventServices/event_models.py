import uuid
import random
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from Application.AuthenticationServices.auth_models import User


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('Community', 'Community Ride'),
        ('Trail', 'Mountain & Trail'),
        ('Race', 'Races & Speed'),
        ('Workshop', 'Workshop'),
    ]
    DIFFICULTY_CHOICES = [
        ('All Levels', 'All Levels'),
        ('Beginner Friendly', 'Beginner Friendly'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.CharField(max_length=100, primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Community')
    category_label = models.CharField(max_length=100, blank=True)
    tag = models.CharField(max_length=50, blank=True, default='Popular')
    date = models.CharField(max_length=100)
    time = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    google_maps_url = models.URLField(max_length=500, blank=True, null=True)
    distance = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, default='Intermediate')
    fee = models.CharField(max_length=100, default='Free Entry')
    is_free = models.BooleanField(default=True)
    max_spots = models.PositiveIntegerField(default=50)
    filled_spots = models.PositiveIntegerField(default=0)
    image = models.CharField(max_length=500)
    description = models.TextField()
    highlights = models.JSONField(default=list, blank=True)
    schedule = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='upcoming')
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    @property
    def spots_left(self):
        return max(0, self.max_spots - self.filled_spots)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "event"
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.id:
            self.id = self.slug

        if not self.category_label:
            self.category_label = dict(self.CATEGORY_CHOICES).get(self.category, self.category)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.date})"


class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('waitlist', 'Waitlist'),
        ('attended', 'Attended'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('not_required', 'Not Required (Free)'),
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('waived', 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_number = models.CharField(max_length=50, unique=True, blank=True, db_index=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='event_registrations')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField()
    participants = models.PositiveIntegerField(default=1)
    bike_type = models.CharField(max_length=100, default='Road Bike')
    experience_level = models.CharField(max_length=100, default='Intermediate')
    emergency_contact = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    agreed_to_terms = models.BooleanField(default=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='confirmed')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='not_required')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Event Registration'
        verbose_name_plural = 'Event Registrations'
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'phone'],
                name='unique_event_phone_registration'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.registration_number:
            year = timezone.now().strftime('%Y')
            while True:
                candidate = f"BR-EVT-{year}-{random.randint(1000, 9999)}"
                if not EventRegistration.objects.filter(registration_number=candidate).exists():
                    self.registration_number = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.registration_number} - {self.full_name} ({self.event.title})"

