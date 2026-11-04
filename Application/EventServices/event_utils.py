from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_event_registration_confirmation(registration):
    """
    Sends an automated email confirmation to the participant upon successful event registration.
    Fails gracefully so that registration flow is never blocked by email provider outages.
    """
    try:
        event = registration.event
        subject = f"Registration Confirmed: {event.title} (Ticket #{registration.registration_number})"
        from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@boatridersports.in')
        to_email = [registration.email]

        text_content = f"""
🚴 Boatrider Sports Event Confirmation

Hi {registration.full_name},
Your registration for "{event.title}" has been confirmed!

🎟️ Ticket Code : #{registration.registration_number}
📅 Date        : {event.date}
⏰ Time        : {event.time}
📍 Location    : {event.location}
👥 Slots       : {registration.participants} Rider(s)
🚴 Bike Type   : {registration.bike_type}
⭐ Experience  : {registration.experience_level}

No online payment is required for this registration.
Please arrive 15 minutes before flag-off with your bicycle and mandatory helmet.

See you at the starting line!
- Team Boatrider Sports
www.boatridersports.in
        """.strip()

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Event Registration Confirmation</title>
</head>
<body style="margin:0; padding:20px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color:#f4f6f8;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; margin:0 auto; background-color:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
    <!-- Header -->
    <tr>
      <td style="background-color:#0d1117; padding:30px 40px; text-align:center;">
        <h1 style="color:#ffffff; margin:0; font-size:24px; font-weight:700; letter-spacing:0.5px;">BOATRIDER SPORTS</h1>
        <p style="color:#00bcd4; margin:6px 0 0; font-size:14px; font-weight:600; text-transform:uppercase; letter-spacing:1px;">Event Confirmation</p>
      </td>
    </tr>
    <!-- Content -->
    <tr>
      <td style="padding:36px 40px;">
        <h2 style="color:#111827; margin:0 0 12px; font-size:20px;">Spot Confirmed, {registration.full_name}! 🚴</h2>
        <p style="color:#4b5563; font-size:15px; line-height:1.6; margin:0 0 24px;">
          You're officially registered for <strong>{event.title}</strong>. No payment is required for this registration.
        </p>

        <!-- Ticket Card -->
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; margin-bottom:28px;">
          <tr>
            <td style="padding:20px 24px;">
              <table width="100%" cellpadding="6" cellspacing="0" style="font-size:14px; color:#334155;">
                <tr>
                  <td style="color:#64748b; width:35%;">Ticket Code:</td>
                  <td style="font-weight:700; color:#0f172a; font-family:monospace; font-size:16px;">{registration.registration_number}</td>
                </tr>
                <tr>
                  <td style="color:#64748b;">Event:</td>
                  <td style="font-weight:600; color:#0f172a;">{event.title}</td>
                </tr>
                <tr>
                  <td style="color:#64748b;">Date & Time:</td>
                  <td style="font-weight:600; color:#0f172a;">{event.date} • {event.time}</td>
                </tr>
                <tr>
                  <td style="color:#64748b;">Location:</td>
                  <td style="color:#0f172a;">{event.location}</td>
                </tr>
                <tr>
                  <td style="color:#64748b;">Riders / Slots:</td>
                  <td style="font-weight:600; color:#0f172a;">{registration.participants}</td>
                </tr>
                <tr>
                  <td style="color:#64748b;">Bike & Level:</td>
                  <td style="color:#0f172a;">{registration.bike_type} ({registration.experience_level})</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>

        <!-- Notice -->
        <div style="background-color:#ecfdf5; border-left:4px solid #10b981; padding:12px 16px; border-radius:4px; margin-bottom:28px;">
          <p style="margin:0; font-size:13px; color:#065f46; line-height:1.5;">
            <strong>Mandatory Checklist:</strong> Helmets are strictly compulsory for all riders. Please arrive 15 minutes before flag-off with your bicycle in good working condition.
          </p>
        </div>

        <p style="color:#6b7280; font-size:14px; line-height:1.5; margin:0;">
          See you at the starting line!<br>
          <strong>Team Boatrider Sports</strong><br>
          <a href="https://boatridersports.in" style="color:#00bcd4; text-decoration:none;">www.boatridersports.in</a>
        </p>
      </td>
    </tr>
    <!-- Footer -->
    <tr>
      <td style="background-color:#f1f5f9; padding:20px 40px; text-align:center; font-size:12px; color:#94a3b8;">
        This is an automated confirmation for your Boatrider Sports event registration.<br>
        © 2026 Boatrider Sports. All rights reserved.
      </td>
    </tr>
  </table>
</body>
</html>
        """.strip()

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)
        logger.info(f"Event confirmation email sent to {registration.email} for ticket {registration.registration_number}")
    except Exception as e:
        logger.error(f"Failed to send event confirmation email to {registration.email}: {e}")

