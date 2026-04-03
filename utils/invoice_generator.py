from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_invoice(invoice_id, client_name, items, total, gst):
    file_name = f"invoice_{invoice_id}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "ATHARV TECH CO.")

    c.setFont("Helvetica", 10)
    c.drawString(30, 770, f"Invoice No: {invoice_id}")
    c.drawString(30, 755, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    c.drawString(30, 730, f"Client: {client_name}")

    y = 700
    for item in items:
        c.drawString(30, y, f"{item['name']} - ₹{item['price']}")
        y -= 20

    c.drawString(30, y-20, f"GST (18%): ₹{gst}")
    c.drawString(30, y-40, f"Total: ₹{total}")

    c.save()
    return file_name
