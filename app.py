import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "atharv_tech_ultimate_2026"

# Database Config
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
db = SQLAlchemy(app)

# Detailed Models
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
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    type = db.Column(db.String(20)) # 'Invoice' or 'Payment'
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    gst_amt = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

ADMIN_EMAIL = "care.atc1@gmail.com"
ADMIN_PASSWORD = "Atharv$321"

# --- MIDDLEWARE: AUTH ---
def is_logged(): return session.get('logged_in')

@app.route('/')
def index():
    if not is_logged(): return render_template('login.html')
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('email') == ADMIN_EMAIL and request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
    return redirect(url_for('index'))

# --- CLIENTS: MANUAL & BULK ---
@app.route('/add-client', methods=['POST'])
def add_client():
    new_c = Client(name=request.form['name'], company=request.form['company'], contact=request.form['contact'], email=request.form['email'], address=request.form['address'], gstin=request.form['gst'])
    db.session.add(new_c)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/bulk-upload', methods=['POST'])
def bulk_upload():
    file = request.files['file']
    if file:
        df = pd.read_excel(file)
        for _, row in df.iterrows():
            if not Client.query.filter_by(email=row['Email']).first():
                c = Client(name=row['Name'], company=row['Company'], contact=row['Contact'], email=row['Email'], address=row['Address'], gstin=row.get('GSTIN', 'N/A'))
                db.session.add(c)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- BILLING: GST, DISCOUNT, ROUND OFF ---
@app.route('/create-bill', methods=['POST'])
def create_bill():
    client_id = request.form['client_id']
    base = float(request.form['amount'])
    disc = float(request.form.get('discount', 0))
    gst_rate = float(request.form.get('gst_rate', 18))
    
    taxable = base - disc
    gst_amt = round(taxable * (gst_rate/100), 2)
    final_total = round(taxable + gst_amt) # Auto Round Off
    
    t = Transaction(client_id=client_id, type='Invoice', amount=final_total, description=request.form['service'], gst_amt=gst_amt, discount=disc)
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- PAYMENTS ---
@app.route('/add-payment', methods=['POST'])
def add_payment():
    t = Transaction(client_id=request.form['client_id'], type='Payment', amount=float(request.form['amount']), description=request.form['note'])
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- PDF ENGINE (AUTO-DOWNLOAD) ---
@app.route('/download-invoice/<int:tid>')
def download_invoice(tid):
    t = Transaction.query.get(tid)
    c = Client.query.get(t.client_id)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 20, "ATHARV TECH CO. - INVOICE", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(100, 10, f"Bill To: {c.company}")
    pdf.cell(90, 10, f"Date: {t.date.strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.cell(190, 10, f"GSTIN: {c.gstin}", ln=True)
    pdf.ln(10)
    pdf.cell(140, 10, "Description", border=1)
    pdf.cell(50, 10, "Total (INR)", border=1, ln=True, align='R')
    pdf.cell(140, 10, t.description, border=1)
    pdf.cell(50, 10, f"{t.amount}", border=1, ln=True, align='R')
    
    out = BytesIO()
    pdf.output(out)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"Invoice_{c.company}_{tid}.pdf", mimetype='application/pdf')

@app.route('/admin')
def admin_dashboard():
    if not is_logged(): return redirect(url_for('login'))
    clients = Client.query.all()
    txs = Transaction.query.all()
    return render_template('admin.html', clients=clients, txs=txs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
