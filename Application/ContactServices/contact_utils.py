from django.conf import settings
from django.core.mail import EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)


def send_contact_email(enquiry):

    subject = f"New Enquiry – {enquiry.subject}"

    from_email = settings.EMAIL_HOST_USER

    to_email = [settings.EMAIL_HOST_USER]

    # ── Plain Text Email ─────────────────────────────

    text_content = f"""
New Contact Enquiry
{'=' * 45}

Enquiry ID : {enquiry.enquiry_id}

Name       : {enquiry.name}
Email      : {enquiry.email}
Phone      : {enquiry.phone}
Subject    : {enquiry.subject}

Message:
{enquiry.message}

Submitted On:
{enquiry.created.strftime('%d %b %Y, %I:%M %p')}

{'=' * 45}
    """.strip()

    # ── HTML Email ──────────────────────────────────

    html_content = f"""
    <html>
    <body style="
        font-family: Arial, sans-serif;
        background: #f4f6f9;
        padding: 20px;
        color: #333;
    ">

        <div style="
            max-width: 650px;
            margin: auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        ">

            <h2 style="
                color: #1a73e8;
                border-bottom: 2px solid #1a73e8;
                padding-bottom: 10px;
                margin-bottom: 25px;
            ">
                📩 New Contact Enquiry
            </h2>

            <table style="
                width:100%;
                border-collapse: collapse;
            ">

                <tr>
                    <td style="padding:10px 0; width:150px;">
                        <strong>Enquiry ID</strong>
                    </td>
                    <td>{enquiry.enquiry_id}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Name</strong>
                    </td>
                    <td>{enquiry.name}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Email</strong>
                    </td>
                    <td>{enquiry.email}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Phone</strong>
                    </td>
                    <td>{enquiry.phone}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Subject</strong>
                    </td>
                    <td>{enquiry.subject}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Submitted</strong>
                    </td>
                    <td>
                        {enquiry.created.strftime('%d %b %Y, %I:%M %p')}
                    </td>
                </tr>

            </table>

            <div style="
                margin-top: 25px;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #1a73e8;
            ">

                <strong>Message</strong>

                <p style="
                    margin-top: 12px;
                    line-height: 1.7;
                    white-space: pre-line;
                ">
                    {enquiry.message}
                </p>

            </div>

            <p style="
                margin-top: 30px;
                font-size: 13px;
                color: #888;
            ">
                This enquiry was submitted through your website contact form.
            </p>

        </div>

    </body>
    </html>
    """

    # ── Send Email ──────────────────────────────────

    try:

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            to_email
        )

        msg.attach_alternative(html_content, "text/html")

        msg.send()

        logger.info(
            "Contact enquiry email sent successfully: %s",
            enquiry.enquiry_id
        )

    except Exception as e:

        logger.error(
            "Failed to send contact enquiry email %s: %s",
            enquiry.enquiry_id,
            e
        )


def send_contact_confirmation_mail(enquiry):
    subject = f"Thank you for your enquiry - {enquiry.subject}"
    from_email = settings.EMAIL_HOST_USER
    to_email = [enquiry.email]
    text_content = f"""
    Dear {enquiry.name},

    Thank you for reaching out to us. We have received your enquiry with the following details:

    Enquiry ID : {enquiry.enquiry_id}

    Name       : {enquiry.name}
    Email      : {enquiry.email}
    Phone      : {enquiry.phone}
    Subject    : {enquiry.subject}

    Message:
    {enquiry.message}

    We will get back to you as soon as possible, typically within 24-48 business hours.

    Best regards,
    Boat Rider Sports
    """
    html_content = f"""
    <html>
    <body style="
        font-family: Arial, sans-serif;
        background: #f4f6f9;
        padding: 20px;
        color: #333;
    ">

        <div style="
            max-width: 650px;
            margin: auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        ">

            <h2 style="
                color: #1a73e8;
                border-bottom: 2px solid #1a73e8;
                padding-bottom: 10px;
                margin-bottom: 25px;
            ">
                📩 Thank you for your enquiry
            </h2>

            <p style="font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                Dear <strong>{enquiry.name}</strong>,
            </p>

            <p style="font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                Thank you for reaching out to us. We have received your enquiry with the following details:
            </p>

            <table style="
                width:100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            ">

                <tr>
                    <td style="padding:10px 0; width:150px;">
                        <strong>Enquiry ID</strong>
                    </td>
                    <td>{enquiry.enquiry_id}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Name</strong>
                    </td>
                    <td>{enquiry.name}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Email</strong>
                    </td>
                    <td>{enquiry.email}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Phone</strong>
                    </td>
                    <td>{enquiry.phone}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Subject</strong>
                    </td>
                    <td>{enquiry.subject}</td>
                </tr>

                <tr>
                    <td style="padding:10px 0;">
                        <strong>Submitted</strong>
                    </td>
                    <td>
                        {enquiry.created.strftime('%d %b %Y, %I:%M %p')}
                    </td>
                </tr>

            </table>

            <div style="
                margin-top: 25px;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #1a73e8;
            ">

                <strong>Your Message</strong>

                <p style="
                    margin-top: 12px;
                    line-height: 1.7;
                    white-space: pre-line;
                ">
                    {enquiry.message}
                </p>

            </div>

            <p style="
                margin-top: 30px;
                font-size: 15px;
                line-height: 1.6;
            ">
                We will get back to you as soon as possible, typically within <strong>24-48 business hours</strong>.
            </p>

            <p style="
                margin-top: 25px;
                font-size: 14px;
                color: #555;
            ">
                Best regards,<br>
                <strong>Boat Rider Sports</strong>
            </p>

        </div>

    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            to_email
        )

        msg.attach_alternative(html_content, "text/html")
        msg.send()

        logger.info(
            "Contact confirmation email sent successfully to %s: %s",
            enquiry.email,
            enquiry.enquiry_id
        )

    except Exception as e:
        logger.error(
            "Failed to send contact confirmation email to %s: %s",
            enquiry.email,
            e
        )


def send_enquiry_notification(enquiry):
    send_contact_email(enquiry)
    send_contact_confirmation_mail(enquiry)