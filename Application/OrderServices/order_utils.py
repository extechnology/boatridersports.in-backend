from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

def generate_invoice_pdf(order, bike_orders, accessories_orders):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "INVOICE")
    
    # Order Info
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Order ID: {order.unique_id}")
    c.drawString(50, height - 100, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, height - 120, f"Status: {order.status}")
    
    # Delivery Address
    addr = order.user_address
    addr_name = getattr(addr, 'name', 'N/A') if addr else 'N/A'
    addr_phone = getattr(addr, 'phone_number', 'N/A') if addr else 'N/A'
    addr_line = f"{getattr(addr, 'address', '')}, {getattr(addr, 'city', '')}" if addr else 'N/A'
    addr_state_pin = f"{getattr(addr, 'state', '')} - {getattr(addr, 'pincode', '')}" if addr else ''

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 150, "Billed To:")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 165, addr_name)
    c.drawString(50, height - 180, addr_phone)
    c.drawString(50, height - 195, addr_line)
    c.drawString(50, height - 210, addr_state_pin)
    
    y = height - 250
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Items")
    c.drawString(400, y, "Qty")
    c.drawString(480, y, "Subtotal")
    y -= 10
    c.line(50, y, 550, y)
    y -= 20
    
    c.setFont("Helvetica", 11)
    
    for item in bike_orders:
        color = item.color.color.color_name if getattr(item, 'color', None) else '–'
        size  = item.size.size if getattr(item, 'size', None) else '–'
        desc = f"{item.bike.name} (Color: {color}, Size: {size})"
        c.drawString(50, y, desc)
        c.drawString(400, y, str(item.quantity))
        c.drawString(480, y, f"Rs. {item.subtotal}")
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)

    for item in accessories_orders:
        desc = item.accessory.name
        c.drawString(50, y, desc)
        c.drawString(400, y, str(item.quantity))
        c.drawString(480, y, f"Rs. {item.subtotal}")
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)
        
    y -= 10
    c.line(50, y, 550, y)
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Total Amount:")
    c.drawString(480, y, f"Rs. {order.total_amount}")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()
    
def order_confirmation_email(order):
    if not order.user or not getattr(order.user, 'email', None):
        logger.warning("No recipient email found for order %s", order.unique_id)
        return

    subject = f'Order Confirmation – #{order.unique_id}'
    from_email = settings.EMAIL_HOST_USER
    to_email = [order.user.email]

    # Fetch related items
    bike_orders       = order.bike_orders.select_related('bike', 'color', 'size').all()
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
    addr_name = getattr(addr, 'name', 'N/A') if addr else 'N/A'
    addr_phone = getattr(addr, 'phone_number', 'N/A') if addr else 'N/A'
    addr_address = getattr(addr, 'address', '') if addr else ''
    addr_city = getattr(addr, 'city', '') if addr else ''
    addr_state = getattr(addr, 'state', '') if addr else ''
    addr_pincode = getattr(addr, 'pincode', '') if addr else ''
    addr_type = getattr(addr, 'address_type', 'Delivery') if addr else 'Delivery'

    # ── Plain-text body ────────────────────────────────────────────
    text_content = f"""
Order Confirmation – #{order.unique_id}
{'=' * 45}
Status     : {order.status}
Order Date : {order.created_at:%d %b %Y, %I:%M %p}
Total Items: {order.total_items}

Delivery Address:
  {addr_name}
  {addr_address}, {addr_city}, {addr_state} – {addr_pincode}
  📞 {addr_phone}

Bikes:
{bikes_text or '  None'}

Accessories:
{accessories_text or '  None'}

{'─' * 45}
Total Amount : ₹{order.total_amount}
{'─' * 45}

Thank you for your order!
    """.strip()

    # ── HTML body ──────────────────────────────────────────────────
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">

        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">
            Order Confirmation
        </h2>

        <table style="margin-bottom: 16px;">
            <tr>
                <td style="padding: 4px 16px 4px 0;"><strong>Order ID</strong></td>
                <td>#{order.unique_id}</td>
            </tr>
            <tr>
                <td style="padding: 4px 16px 4px 0;"><strong>Status</strong></td>
                <td><span style="background:#fff3cd;padding:2px 8px;border-radius:4px;">{order.status}</span></td>
            </tr>
            <tr>
                <td style="padding: 4px 16px 4px 0;"><strong>Order Date</strong></td>
                <td>{order.created_at:%d %b %Y, %I:%M %p}</td>
            </tr>
        </table>

        <!-- Delivery Address -->
        <div style="background:#f5f5f5; padding:12px 16px; border-radius:6px; margin-bottom:20px;">
            <strong>📦 Delivery Address</strong><br>
            {addr_name} &nbsp;|&nbsp; 📞 {addr_phone}<br>
            {addr_address}, {addr_city}, {addr_state.title() if addr_state else ''} – {addr_pincode}
            &nbsp;<span style="background:#e8f5e9;padding:1px 7px;border-radius:3px;font-size:12px;">{addr_type}</span>
        </div>

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

        <p style="margin-top:24px; color:#555;">Thank you for your order! 🎉</p>
    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        
        # Attach PDF Invoice
        pdf_data = generate_invoice_pdf(order, bike_orders, accessories_orders)
        
        # Save to model
        from django.core.files.base import ContentFile
        order.invoice.save(f"invoice_{order.unique_id}.pdf", ContentFile(pdf_data), save=True)
        
        msg.attach(f"invoice_{order.unique_id}.pdf", pdf_data, "application/pdf")
        
        msg.send()
        logger.info("Order confirmation email sent for order %s (with invoice)", order.unique_id)
    except Exception as e:
        logger.error("Failed to send email for order %s: %s", order.unique_id, e)


def process_order_success(user_order, payment_id=None, signature=None):
    """
    Fulfills the order idempotently:
    1. Updates status to 'Processing' and payment_status to True
    2. Saves razorpay payment ID and signature if provided
    3. Decrements stock for bikes and accessories
    4. Generates invoice & sends confirmation email
    5. Clears the user's cart
    """
    if user_order.payment_status:
        logger.info("Order %s already marked as paid. Skipping duplicate processing.", user_order.unique_id)
        return user_order

    from Application.OrderServices.order_models import BikeOrderItems, AccessoriesOrderItems
    from Application.CartServices.usercart_models import UserCartModel

    user_order.status = 'Processing'
    user_order.payment_status = True
    if payment_id:
        user_order.razorpay_payment_id = payment_id
    if signature:
        user_order.razorpay_signature = signature
    user_order.save()

    # Update bike stock
    bike_items = BikeOrderItems.objects.filter(order=user_order)
    for item in bike_items:
        if item.bike:
            if item.bike.stock >= item.quantity:
                item.bike.stock -= item.quantity
            else:
                item.bike.stock = 0
            item.bike.save()

    # Update accessory stock
    accessory_items = AccessoriesOrderItems.objects.filter(order=user_order)
    for item in accessory_items:
        if item.accessory:
            if item.accessory.stock >= item.quantity:
                item.accessory.stock -= item.quantity
            else:
                item.accessory.stock = 0
            item.accessory.save()

    # Send confirmation email (with generated PDF invoice)
    try:
        order_confirmation_email(user_order)
    except Exception as e:
        logger.error("Failed to send order confirmation email for %s: %s", user_order.unique_id, e)

    # Clear user cart
    try:
        cart = UserCartModel.objects.get(user=user_order.user)
        cart.delete()
    except UserCartModel.DoesNotExist:
        pass

    return user_order


def order_cancellation_email(order, reason=None):
    if not order.user or not getattr(order.user, 'email', None):
        logger.warning("No recipient email found for order %s", order.unique_id)
        return

    status_label = "Cancelled" if order.status == "Cancelled" else "Payment Failed"
    subject = f"Order {status_label} – #{order.unique_id}"
    from_email = settings.EMAIL_HOST_USER
    to_email = [order.user.email]

    # Fetch related items
    bike_orders = order.bike_orders.select_related('bike', 'color', 'size').all()
    accessories_orders = order.accessories_orders.select_related('accessory').all()

    # HTML snippets
    def bike_row_html(item):
        color = item.color.color.color_name if item.color else '–'
        size = item.size.size if item.size else '–'
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

    bikes_html = ''.join(bike_row_html(i) for i in bike_orders)
    accessories_html = ''.join(accessory_row_html(i) for i in accessories_orders)

    # Plain-text snippets
    def bike_row_text(item):
        color = item.color.color.color_name if item.color else '–'
        size = item.size.size if item.size else '–'
        return f'  • {item.bike.name} (Color: {color}, Size: {size}) x{item.quantity} — ₹{item.subtotal}'

    def accessory_row_text(item):
        return f'  • {item.accessory.name} x{item.quantity} — ₹{item.subtotal}'

    bikes_text = '\n'.join(bike_row_text(i) for i in bike_orders)
    accessories_text = '\n'.join(accessory_row_text(i) for i in accessories_orders)

    addr = order.user_address
    addr_name = getattr(addr, 'name', 'N/A') if addr else 'N/A'
    addr_phone = getattr(addr, 'phone_number', 'N/A') if addr else 'N/A'
    addr_address = getattr(addr, 'address', '') if addr else ''
    addr_city = getattr(addr, 'city', '') if addr else ''
    addr_state = getattr(addr, 'state', '') if addr else ''
    addr_pincode = getattr(addr, 'pincode', '') if addr else ''
    addr_type = getattr(addr, 'address_type', 'Delivery') if addr else 'Delivery'

    reason_line = f"Reason     : {reason}\n" if reason else ""
    reason_banner = f"<p style='margin:6px 0 0 0; font-size:13px; color:#c53030;'><strong>Reason:</strong> {reason}</p>" if reason else ""

    text_content = f"""
Order {status_label} – #{order.unique_id}
{'=' * 45}
Status     : {order.status}
Order Date : {order.created_at:%d %b %Y, %I:%M %p}
Total Items: {order.total_items}
{reason_line}
Delivery Address:
  {addr_name}
  {addr_address}, {addr_city}, {addr_state} – {addr_pincode}
  📞 {addr_phone}

Items:
Bikes:
{bikes_text or '  None'}

Accessories:
{accessories_text or '  None'}

{'─' * 45}
Total Amount : ₹{order.total_amount}
{'─' * 45}

Your order was not completed. If any amount was debited from your account or card, it will be automatically refunded by your payment provider within 5–7 business days.

Thank you,
BoatRider Sports
    """.strip()

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
        <h2 style="color: #e53e3e; border-bottom: 2px solid #e53e3e; padding-bottom: 8px;">
            Order {status_label}
        </h2>

        <div style="background:#fff5f5; border-left: 4px solid #e53e3e; padding: 12px 16px; margin-bottom: 16px; border-radius: 4px;">
            <p style="margin:0; font-size: 14px; color: #c53030;">
                Your order <strong>#{order.unique_id}</strong> has been marked as <strong>{order.status}</strong>.
            </p>
            {reason_banner}
            <p style="margin: 6px 0 0 0; font-size: 13px; color: #742a2a;">
                No invoice is generated for cancelled or uncompleted orders. If your bank account was debited, the amount will be refunded within 5–7 business days.
            </p>
        </div>

        <table style="margin-bottom: 16px;">
            <tr>
                <td style="padding: 4px 16px 4px 0;"><strong>Order ID</strong></td>
                <td>#{order.unique_id}</td>
            </tr>
            <tr>
                <td style="padding: 4px 16px 4px 0;"><strong>Status</strong></td>
                <td><span style="background:#fed7d7; color:#9b2c2c; padding:2px 8px; border-radius:4px; font-weight:bold;">{order.status}</span></td>
            </tr>
            <tr>
                <td style="padding: 4px 16px 4px 0;"><strong>Order Date</strong></td>
                <td>{order.created_at:%d %b %Y, %I:%M %p}</td>
            </tr>
        </table>

        <!-- Delivery Address -->
        <div style="background:#f5f5f5; padding:12px 16px; border-radius:6px; margin-bottom:20px;">
            <strong>📦 Delivery Address</strong><br>
            {addr_name} &nbsp;|&nbsp; 📞 {addr_phone}<br>
            {addr_address}, {addr_city}, {addr_state.title() if addr_state else ''} – {addr_pincode}
            &nbsp;<span style="background:#e8f5e9;padding:1px 7px;border-radius:3px;font-size:12px;">{addr_type}</span>
        </div>

        <!-- Bikes -->
        {"" if not bike_orders else f'''
        <h3 style="color:#333; margin-bottom:8px;">🚲 Bikes</h3>
        <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
            <thead>
                <tr style="background:#718096; color:#fff;">
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
                <tr style="background:#718096; color:#fff;">
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
                    border-top:2px solid #eee; padding-top:12px; color:#e53e3e;">
            Total: ₹{order.total_amount}
        </div>

        <p style="margin-top:24px; color:#555;">
            Thank you for visiting BoatRider Sports. Please feel free to place a new order at your convenience.
        </p>
    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        # Notice: NO PDF attachment is generated or attached!
        msg.send()
        logger.info("Order cancellation email sent for order %s (no invoice attached)", order.unique_id)
    except Exception as e:
        logger.error("Failed to send cancellation email for order %s: %s", order.unique_id, e)


def process_order_cancellation(user_order, reason=None, status_name='Cancelled'):
    """
    Cancels or fails the order and sends notification email WITHOUT invoice:
    1. Skips if the order is already marked as paid
    2. Updates order status to status_name ('Cancelled' or 'Failed')
    3. Sends cancellation/failure email without invoice attachment
    """
    if user_order.payment_status:
        logger.warning("Order %s is already paid. Skipping cancellation.", user_order.unique_id)
        return user_order

    user_order.status = status_name
    user_order.save()

    try:
        order_cancellation_email(user_order, reason=reason)
    except Exception as e:
        logger.error("Failed to send order cancellation email for %s: %s", user_order.unique_id, e)

    return user_order

