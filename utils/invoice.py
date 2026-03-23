from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm

def generate_invoice_pdf(order, order_items, seller, customer):

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    c = canvas.Canvas(file.name, pagesize=A4)

    # -----------------------
    # HEADER
    # -----------------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "GST INVOICE")

    c.setFont("Helvetica", 10)

    # -----------------------
    # ORDER DETAILS
    # -----------------------
    invoice_no = order.invoice_number or f"INV-{order.id}"

    c.drawString(50, 770, f"Invoice No: {invoice_no}")
    c.drawString(50, 755, f"Order ID: {order.id}")
    c.drawString(50, 740, f"Date: {order.created_at.strftime('%d-%m-%Y')}")

    # ✅ BARCODE (FIXED INDENTATION)
    barcode = code128.Code128(invoice_no, barHeight=20 * mm, barWidth=0.5)
    barcode.drawOn(c, 400, 760)

    # -----------------------
    # SELLER DETAILS
    # -----------------------
    c.drawString(50, 710, f"Seller: {seller.shop_name or 'N/A'}")
    c.drawString(50, 695, f"GST No: {seller.gst_no or 'N/A'}")
    c.drawString(50, 680, f"Address: {seller.address or 'N/A'}")

    # -----------------------
    # CUSTOMER DETAILS
    # -----------------------
    c.drawString(50, 650, f"Customer: {customer.name}")
    c.drawString(50, 635, f"Phone: {customer.phone}")
    c.drawString(50, 620, f"Email: {customer.email}")

    c.drawString(
        50, 605,
        f"Address: {customer.address or ''}, {customer.state or ''} - {customer.pincode or ''}"
    )

    # -----------------------
    # TABLE HEADER
    # -----------------------
    y = 570
    c.setFont("Helvetica-Bold", 10)

    c.drawString(50, y, "Product")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Price")
    c.drawString(370, y, "Total")

    y -= 20
    c.setFont("Helvetica", 10)

    total = 0

    # -----------------------
    # ITEMS
    # -----------------------
    for item in order_items:
        line_total = item.qty * item.price
        total += line_total

        product_name = item.product.name if item.product else "Item"

        c.drawString(50, y, product_name)
        c.drawString(250, y, str(item.qty))
        c.drawString(300, y, f"₹{item.price}")
        c.drawString(370, y, f"₹{line_total}")

        y -= 20

    # -----------------------
    # GST CALCULATION
    # -----------------------
    cgst = round(total * 0.09, 2)
    sgst = round(total * 0.09, 2)
    grand_total = round(total + cgst + sgst, 2)

    y -= 20
    c.drawString(300, y, f"Subtotal: ₹{total}")

    y -= 15
    c.drawString(300, y, f"CGST (9%): ₹{cgst}")

    y -= 15
    c.drawString(300, y, f"SGST (9%): ₹{sgst}")

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, y, f"Grand Total: ₹{grand_total}")

    # -----------------------
    # FOOTER
    # -----------------------
    y -= 40
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Thank you for your purchase!")
    c.drawString(50, y - 15, "This is a computer generated invoice.")

    c.save()

    return file.name