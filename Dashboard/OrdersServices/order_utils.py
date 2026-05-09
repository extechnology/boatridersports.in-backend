from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


def order_updation_mail(order):

    # ── Status mapping for email ──────────────────────────────
    STATUS_MAP = {
        "Pending":     "⏳ Pending",
        "Processing":  "⚙️ Processing",
        "Shipped":     "🚚 Shipped",
        "Delivered":   "✅ Delivered",
        "Cancelled":   "❌ Cancelled",
        "Failed":      "⚠️ Failed",
    }

    current_status = STATUS_MAP.get(order.status, order.status)

    subject = f"Order #{order.unique_id} has been updated to {current_status}"
    from_email = settings.EMAIL_HOST_USER
    to_email = [order.user.email]

    # ── Fetch related items ────────────────────────────────────────
    bike_orders        = order.bike_orders.select_related('bike', 'color', 'size').all()
    accessories_orders = order.accessories_orders.select_related('accessory').all()

    # ── HTML snippets ──────────────────────────────────────────────
    def bike_row_html(item):
        color = item.color.color.color_name if item.color else '–'
        size  = item.size.size        if item.size  else '–'
        return (
            f'<tr>'
            f'<td style="padding:6px 12px 6px 0;">{item.bike.name}</td>'
            f'<td style="padding:6px 12px;">Color: {color} / Size: {size}</td>'
            f'<td style="padding:6px 12px;">×{item.quantity}</td>'
            f'<td style="padding:6px 0; text-align:right;">₹{item.subtotal}</td>'
            f'</tr>'
        )

    def accessory_row_html(item):
        return (
            f'<tr>'
            f'<td style="padding:6px 12px 6px 0;">{item.accessory.name}</td>'
            f'<td style="padding:6px 12px;">–</td>'
            f'<td style="padding:6px 12px;">×{item.quantity}</td>'
            f'<td style="padding:6px 0; text-align:right;">₹{item.subtotal}</td>'
            f'</tr>'
        )

    bikes_html       = ''.join(bike_row_html(i)      for i in bike_orders)
    accessories_html = ''.join(accessory_row_html(i) for i in accessories_orders)

    # ── Plain-text snippets ────────────────────────────────────────
    def bike_row_text(item):
        color = item.color.color.color_name if item.color else '–'
        size  = item.size.size        if item.size  else '–'
        return f'  • {item.bike.name} (Color: {color}, Size: {size}) x{item.quantity} — ₹{item.subtotal}'

    def accessory_row_text(item):
        return f'  • {item.accessory.name} x{item.quantity} — ₹{item.subtotal}'

    bikes_text       = '\n'.join(bike_row_text(i)      for i in bike_orders)
    accessories_text = '\n'.join(accessory_row_text(i) for i in accessories_orders)

    # Delivery address
    addr = order.user_address

    # ── Plain-text body ────────────────────────────────────────────
    text_content = f"""
Order #{order.unique_id} has been updated to {current_status}
{'=' * 50}
Order ID   : {order.unique_id}
Status     : {current_status}
Order Date : {order.created_at:%d %b %Y, %I:%M %p}
Total Items: {order.total_items}

Delivery Address:
  {addr.name}
  {addr.address}, {addr.city}, {addr.state} – {addr.pincode}
  📞 {addr.phone_number}

Bikes:
{bikes_text or '  None'}

Accessories:
{accessories_text or '  None'}

{'─' * 50}
Total Amount : ₹{order.total_amount}
{'─' * 50}
    """.strip()

    # ── HTML body ──────────────────────────────────────────────────
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">

        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">
            Order #{order.unique_id} Status Update
        </h2>

        <div style="background:#f5f5f5; padding:12px 16px; border-radius:6px; margin-bottom:20px;">
            <strong>Current Status:</strong> <span style="font-weight:bold;">{current_status}</span>
            <br>Updated on: {order.updated_at:%d %b %Y, %I:%M %p}
        </div>

        <!-- Delivery Address -->
        <div style="background:#f5f5f5; padding:12px 16px; border-radius:6px; margin-bottom:20px;">
            <strong>📦 Delivery Address</strong><br>
            {addr.name} &nbsp;|&nbsp; 📞 {addr.phone_number}<br>
            {addr.address}, {addr.city}, {addr.state.title()} – {addr.pincode}
            &nbsp;<span style="background:#e8f5e9;padding:1px 7px;border-radius:3px;font-size:12px;">{addr.address_type}</span>
        </div>
        {"" if order.tracking_id is None else f'''
        <!-- Shipment Details -->
        <div style="background:#f5f5f5; padding:12px 16px; border-radius:6px; margin-bottom:20px;">
            <strong>📦 Shipped Via: {order.shipped_via}</strong><br>
            <strong>📦 Tracking ID: {order.tracking_id}</strong><br>
            
        </div>
        '''}

        <!-- Bikes -->
        {"" if not bike_orders else f'''
        <h3 style="color:#333; margin-bottom:8px;">🚲 Bikes</h3>
        <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
            <thead>
                <tr style="background:#1a73e8; color:#fff;">
                    <th style="padding:8px 12px; text-align:left;">Item</th>
                    <th style="padding:8px 12px; text-align:left;">Variant</th>
                    <th style="padding:8px 12px; text-align:left;">Qty</th>
                    <th style="padding:8px 12px; text-align:right;">Subtotal</th>
                </tr>
            </thead>
            <tbody>{bikes_html}</tbody>
        </table>
        '''}

        <!-- Accessories -->
        {"" if not accessories_orders else f'''
        <h3 style="color:#333; margin-bottom:8px;">🔧 Accessories</h3>
        <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
            <thead>
                <tr style="background:#1a73e8; color:#fff;">
                    <th style="padding:8px 12px; text-align:left;">Item</th>
                    <th style="padding:8px 12px; text-align:left;">–</th>
                    <th style="padding:8px 12px; text-align:left;">Qty</th>
                    <th style="padding:8px 12px; text-align:right;">Subtotal</th>
                </tr>
            </thead>
            <tbody>{accessories_html}</tbody>
        </table>
        '''}

        <!-- Total -->
        <div style="text-align:right; font-size:18px; font-weight:bold;
                    border-top:2px solid #eee; padding-top:12px; color:#1a73e8;">
            Total: ₹{order.total_amount}
        </div>

        <p style="margin-top:24px; color:#555;">Thanks for shopping with us!</p>

        <div style="margin-top:30px; padding-top:15px; border-top:1px solid #eee;">
            <small style="color:#777;">
                Questions? Contact us at: {settings.EMAIL_HOST_USER}<br>
                Or call: +91 XXX XXX XXXX
            </small>
        </div>
    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info("Order update email sent for order %s to %s", order.unique_id, order.user.email)
    except Exception as e:
        logger.error("Failed to send order update email for order %s: %s", order.unique_id, e)