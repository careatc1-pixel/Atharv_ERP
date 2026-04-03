import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "atharv_only_billing_2026"

# Database setup
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(current_dir, 'billing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inv_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(150))
    client_gst = db.Column(db.String(50))
    items_data = db.Column(db.Text) # JSON String
    total_amt = db.Column(db.Float)
    gst_amt = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()
    return render_template('admin.html', invoices=invoices)

@app.route('/login', methods=['POST'])
def login():
    if request.form['email'] == "care.atc1@gmail.com" and request.form['password'] == "Atharv$321":
        session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    client = request.form.get('client_name')
    gst_no = request.form.get('gst_no')
    services = request.form.getlist('service[]')
    prices = request.form.getlist('price[]')
    gst_rate = float(request.form.get('gst_rate', 18))
    
    items = []
    subtotal = 0
    for s, p in zip(services, prices):
        if s and p:
            items.append({"desc": s, "amt": float(p)})
            subtotal += float(p)
    
    tax = round(subtotal * (gst_rate / 100), 2)
    grand_total = round(subtotal + tax)
    
    new_inv_no = f"ATC/INV/{Invoice.query.count() + 1:03d}"
    
    inv = Invoice(inv_no=new_inv_no, client_name=client, client_gst=gst_no, 
                  items_data=json.dumps(items), total_amt=grand_total, gst_amt=tax)
    db.session.add(inv)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/download/<int:id>')
def download(id):
    inv = Invoice.query.get(id)
    items = json.loads(inv.items_data)
    
    pdf = FPDF()
    pdf.add_page()
    # Blue Header
    pdf.set_fill_color(0, 51, 102); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 24)
    pdf.cell(190, 20, "ATHARV TECH CO.", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.ln(20); pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, f"INVOICE: {inv.inv_no}"); pdf.cell(90, 10, f"DATE: {inv.date.strftime('%d-%m-%Y')}", ln=True, align='R')
    
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(100, 5, "BILL TO:"); pdf.ln(5)
    pdf.set_font("Arial", '', 10); pdf.cell(100, 5, f"{inv.client_name}"); pdf.ln(5)
    pdf.cell(100, 5, f"GSTIN: {inv.client_gst}"); pdf.ln(10)
    
    # Table
    pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 10, " Description", 1, 0, 'L', True); pdf.cell(50, 10, " Amount", 1, 1, 'R', True)
    
    pdf.set_font("Arial", '', 10)
    for i in items:
        pdf.cell(140, 10, f" {i['desc']}", 1); pdf.cell(50, 10, f" {i['amt']} ", 1, 1, 'R')
    
    pdf.ln(5); pdf.cell(140, 8, "Tax Amount:", align='R'); pdf.cell(50, 8, f"{inv.gst_amt}", ln=True, align='R')
    pdf.set_font("Arial", 'B', 12); pdf.cell(140, 10, "GRAND TOTAL:", align='R'); pdf.cell(50, 10, f"Rs. {inv.total_amt}", ln=True, align='R')
    
    out = BytesIO(); pdf.output(out); out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"{inv.inv_no}.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
