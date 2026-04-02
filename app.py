import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
import json

app = Flask(__name__)
app.secret_key = "atharv_tech_billing_v3"

# Database Configuration
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    company = db.Column(db.String(150))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    items_json = db.Column(db.Text) # Storing multiple services as JSON string
    discount = db.Column(db.Float, default=0.0)
    gst_amt = db.Column(db.Float)
    grand_total = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    clients = Client.query.all()
    invoices = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('admin.html', clients=clients, invoices=invoices)

# --- CLIENT MODULE (Existing) ---
@app.route('/add-client', methods=['POST'])
def add_client():
    c = Client(name=request.form['name'], company=request.form['company'], contact=request.form['contact'], email=request.form['email'], address=request.form['address'], gstin=request.form['gst'])
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('index'))

# --- BILLING MODULE (New) ---
@app.route('/generate-bill', methods=['POST'])
def generate_bill():
    client_id = request.form['client_id']
    services = request.form.getlist('service[]')
    prices = request.form.getlist('price[]')
    discount = float(request.form.get('discount', 0))
    
    items = []
    subtotal = 0
    for s, p in zip(services, prices):
        if s and p:
            items.append({"desc": s, "amt": float(p)})
            subtotal += float(p)
    
    taxable = subtotal - discount
    gst = round(taxable * 0.18, 2)
    total = round(taxable + gst) # Auto Round Off
    
    inv_count = Transaction.query.count() + 1
    inv_no = f"ATC/26-27/{inv_count:03d}"
    
    new_inv = Transaction(
        invoice_no=inv_no,
        client_id=client_id,
        items_json=json.dumps(items),
        discount=discount,
        gst_amt=gst,
        grand_total=total
    )
    db.session.add(new_inv)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/download-pdf/<int:id>')
def download_pdf(id):
    inv = Transaction.query.get(id)
    client = Client.query.get(inv.client_id)
    items = json.loads(inv.items_json)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "ATHARV TECH CO.", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, "Software & Automation Experts", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, f"Invoice No: {inv.invoice_no}")
    pdf.cell(90, 10, f"Date: {inv.date.strftime('%d-%m-%Y')}", ln=True, align='R')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 5, "BILL TO:")
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 5, f"{client.company}")
    pdf.ln(5)
    pdf.cell(100, 5, f"GSTIN: {client.gstin}")
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 10, " Description", border=1, fill=True)
    pdf.cell(50, 10, " Amount (Rs)", border=1, ln=True, fill=True, align='R')
    
    pdf.set_font("Arial", '', 10)
    subtotal = 0
    for item in items:
        pdf.cell(140, 10, f" {item['desc']}", border=1)
        pdf.cell(50, 10, f" {item['amt']} ", border=1, ln=True, align='R')
        subtotal += item['amt']
        
    pdf.ln(5)
    pdf.cell(140, 8, "Subtotal:", align='R')
    pdf.cell(50, 8, f"{subtotal}", ln=True, align='R')
    pdf.cell(140, 8, "Discount:", align='R')
    pdf.cell(50, 8, f"-{inv.discount}", ln=True, align='R')
    pdf.cell(140, 8, "GST (18%):", align='R')
    pdf.cell(50, 8, f"+{inv.gst_amt}", ln=True, align='R')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, "GRAND TOTAL:", align='R')
    pdf.cell(50, 10, f"Rs. {inv.grand_total}", ln=True, align='R')
    
    out = BytesIO()
    pdf.output(out)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"{inv.invoice_no}.pdf", mimetype='application/pdf')

# Login/Logout same as before
@app.route('/login', methods=['POST'])
def login():
    if request.form['email'] == "care.atc1@gmail.com" and request.form['password'] == "Atharv$321":
        session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
