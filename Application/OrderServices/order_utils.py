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
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 150, "Billed To:")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 165, addr.name)
    c.drawString(50, height - 180, addr.phone_number)
    c.drawString(50, height - 195, f"{addr.address}, {addr.city}")
    c.drawString(50, height - 210, f"{addr.state} - {addr.pincode}")
    
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

    # ── Plain-text body ────────────────────────────────────────────
    text_content = f"""
Order Confirmation – #{order.unique_id}
{'=' * 45}
Status     : {order.status}
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
            {addr.name} &nbsp;|&nbsp; 📞 {addr.phone_number}<br>
            {addr.address}, {addr.city}, {addr.state.title()} – {addr.pincode}
            &nbsp;<span style="background:#e8f5e9;padding:1px 7px;border-radius:3px;font-size:12px;">{addr.address_type}</span>
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
        logger.info("Order confirmation email sent for order %s", order.unique_id)
    except Exception as e:
        logger.error("Failed to send email for order %s: %s", order.unique_id, e)