from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm
import tempfile


def generate_invoice_pdf(order, order_items, seller, customer):

    # Create temporary PDF file
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    # Create canvas
    c = canvas.Canvas(file.name, pagesize=A4)

    # =====================================================
    # HEADER
    # =====================================================

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "GST INVOICE")

    c.setFont("Helvetica", 10)

    # =====================================================
    # ORDER DETAILS
    # =====================================================

    invoice_no = getattr(order, "invoice_number", None) or f"INV-{order.id}"

    order_date = (
        order.created_at.strftime("%d-%m-%Y")
        if getattr(order, "created_at", None)
        else "N/A"
    )

    c.drawString(50, 770, f"Invoice No: {invoice_no}")
    c.drawString(50, 755, f"Order ID: {order.id}")
    c.drawString(50, 740, f"Date: {order_date}")

    # =====================================================
    # BARCODE
    # =====================================================

    barcode = code128.Code128(
        invoice_no,
        barHeight=20 * mm,
        barWidth=0.5
    )

    barcode.drawOn(c, 400, 760)

    # =====================================================
    # SELLER DETAILS
    # =====================================================

    seller_name = getattr(seller, "shop_name", "N/A")
    seller_gst = getattr(seller, "gst_no", "N/A")
    seller_address = getattr(seller, "address", "N/A")

    c.drawString(50, 710, f"Seller: {seller_name}")
    c.drawString(50, 695, f"GST No: {seller_gst}")
    c.drawString(50, 680, f"Address: {seller_address}")

    # =====================================================
    # CUSTOMER DETAILS
    # =====================================================

    customer_name = getattr(customer, "name", "N/A")
    customer_phone = getattr(customer, "phone", "N/A")
    customer_email = getattr(customer, "email", "N/A")
    customer_address = getattr(customer, "address", "")
    customer_state = getattr(customer, "state", "")
    customer_pincode = getattr(customer, "pincode", "")

    c.drawString(50, 650, f"Customer: {customer_name}")
    c.drawString(50, 635, f"Phone: {customer_phone}")
    c.drawString(50, 620, f"Email: {customer_email}")

    full_address = (
        f"{customer_address}, "
        f"{customer_state} - "
        f"{customer_pincode}"
    )

    c.drawString(50, 605, f"Address: {full_address}")

    # =====================================================
    # TABLE HEADER
    # =====================================================

    y = 570

    c.setFont("Helvetica-Bold", 10)

    c.drawString(50, y, "Product")
    c.drawString(250, y, "Qty")
    c.drawString(320, y, "Price")
    c.drawString(420, y, "Total")

    y -= 20

    c.setFont("Helvetica", 10)

    total = 0

    # =====================================================
    # ORDER ITEMS
    # =====================================================

    for item in order_items:

        qty = getattr(item, "qty", 0)
        price = getattr(item, "price", 0)

        line_total = qty * price

        total += line_total

        product_name = "Item"

        if getattr(item, "product", None):
            product_name = getattr(item.product, "name", "Item")

        c.drawString(50, y, str(product_name))
        c.drawString(250, y, str(qty))
        c.drawString(320, y, f"₹{price}")
        c.drawString(420, y, f"₹{line_total}")

        y -= 20

        # Prevent content overflow
        if y < 100:
            c.showPage()
            y = 800

    # =====================================================
    # GST CALCULATION
    # =====================================================

    cgst = round(total * 0.09, 2)
    sgst = round(total * 0.09, 2)

    grand_total = round(total + cgst + sgst, 2)

    y -= 20

    c.drawString(320, y, f"Subtotal: ₹{total}")

    y -= 15
    c.drawString(320, y, f"CGST (9%): ₹{cgst}")

    y -= 15
    c.drawString(320, y, f"SGST (9%): ₹{sgst}")

    y -= 25

    c.setFont("Helvetica-Bold", 12)

    c.drawString(320, y, f"Grand Total: ₹{grand_total}")

    # =====================================================
    # FOOTER
    # =====================================================

    y -= 50

    c.setFont("Helvetica", 9)

    c.drawString(50, y, "Thank you for your purchase!")
    c.drawString(
        50,
        y - 15,
        "This is a computer generated invoice."
    )

    # Save PDF
    c.save()

    # Return PDF path
    return file.name