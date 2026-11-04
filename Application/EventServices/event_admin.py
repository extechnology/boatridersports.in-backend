import csv
from django.contrib import admin
from django.http import HttpResponse
from .event_models import Event, EventRegistration


@admin.action(description="Export Selected Registrations to CSV")
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="event_attendees.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Microsoft Excel

    writer = csv.writer(response)
    writer.writerow([
        'Ticket Code',
        'Event',
        'Full Name',
        'Phone',
        'Email',
        'Slots',
        'Bike Type',
        'Experience',
        'Emergency Contact',
        'Special Notes',
        'Status',
        'Payment Status',
        'Registration Date'
    ])
    for reg in queryset.select_related('event'):
        writer.writerow([
            reg.registration_number,
            reg.event.title,
            reg.full_name,
            reg.phone,
            reg.email,
            reg.participants,
            reg.bike_type,
            reg.experience_level,
            reg.emergency_contact,
            reg.notes,
            reg.status,
            reg.payment_status,
            reg.created_at.strftime('%Y-%m-%d %H:%M') if reg.created_at else 'N/A'
        ])
    return response


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    fields = ('registration_number', 'full_name', 'phone', 'email', 'participants', 'bike_type', 'status', 'created_at')
    readonly_fields = ('registration_number', 'created_at')
    show_change_link = True
    can_delete = False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'difficulty', 'max_spots', 'filled_spots', 'spots_left', 'status', 'is_published')
    list_filter = ('category', 'difficulty', 'status', 'is_published')
    search_fields = ('title', 'location', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventRegistrationInline]


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'event', 'full_name', 'phone', 'participants', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'event', 'payment_status', 'created_at')
    search_fields = ('registration_number', 'full_name', 'phone', 'email')
    readonly_fields = ('registration_number', 'created_at', 'updated_at')
    actions = [export_as_csv]

