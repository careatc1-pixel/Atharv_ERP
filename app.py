import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "atharv_pro_max_2026"

# Database
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
db = SQLAlchemy(app)

# Models
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name, company = db.Column(db.String(100)), db.Column(db.String(150))
    contact, email = db.Column(db.String(20)), db.Column(db.String(100), unique=True)
    address, gstin = db.Column(db.Text), db.Column(db.String(20))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doc_no = db.Column(db.String(50)) # INV-001 or REC-001
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    type = db.Column(db.String(20)) # 'Invoice' or 'Payment'
    amount = db.Column(db.Float)
    gst_amt, discount = db.Column(db.Float, default=0.0), db.Column(db.Float, default=0.0)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON) # Multiple Services stored here

with app.app_context(): db.create_all()

# --- ROUTES ---
@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    clients = Client.query.all()
    txs = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('admin.html', clients=clients, txs=txs)

@app.route('/login', methods=['POST'])
def login():
    if request.form['email'] == "care.atc1@gmail.com" and request.form['password'] == "Atharv$321":
        session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/add-client', methods=['POST'])
def add_client():
    c = Client(name=request.form['name'], company=request.form['company'], contact=request.form['contact'], email=request.form['email'], address=request.form['address'], gstin=request.form['gst'])
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/create-bill', methods=['POST'])
def create_bill():
    services = request.form.getlist('service[]')
    prices = request.form.getlist('price[]')
    items = [{"service": s, "price": float(p)} for s, p in zip(services, prices)]
    
    subtotal = sum(item['price'] for item in items)
    disc = float(request.form.get('discount', 0))
    taxable = subtotal - disc
    gst = round(taxable * 0.18, 2)
    final = round(taxable + gst)
    
    inv_count = Transaction.query.filter_by(type='Invoice').count() + 1
    t = Transaction(doc_no=f"ATC/INV/{inv_count:03d}", client_id=request.form['client_id'], type='Invoice', amount=final, gst_amt=gst, discount=disc, details=items)
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add-payment', methods=['POST'])
def add_payment():
    rec_count = Transaction.query.filter_by(type='Payment').count() + 1
    t = Transaction(doc_no=f"ATC/REC/{rec_count:03d}", client_id=request.form['client_id'], type='Payment', amount=float(request.form['amount']), details=[{"note": request.form['note']}])
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/download-doc/<int:tid>')
def download_doc(tid):
    t = Transaction.query.get(tid)
    c = Client.query.get(t.client_id)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "ATHARV TECH CO.", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, f"{t.type.upper()} NO: {t.doc_no} | DATE: {t.date.strftime('%d-%m-%Y')}", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(100, 5, f"BILL TO: {c.company}")
    pdf.ln(10)
    
    # Table for multiple items
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 8, "Description", border=1)
    pdf.cell(50, 8, "Amount", border=1, ln=True)
    pdf.set_font("Arial", '', 10)
    
    if t.type == 'Invoice':
        for item in t.details:
            pdf.cell(140, 8, item['service'], border=1)
            pdf.cell(50, 8, f"{item['price']}", border=1, ln=True)
        pdf.ln(5)
        pdf.cell(140, 8, "Discount:", align='R')
        pdf.cell(50, 8, f"-{t.discount}", ln=True)
        pdf.cell(140, 8, "GST (18%):", align='R')
        pdf.cell(50, 8, f"+{t.gst_amt}", ln=True)
    else:
        pdf.cell(140, 8, f"Payment Received: {t.details[0].get('note','')}", border=1)
        pdf.cell(50, 8, f"{t.amount}", border=1, ln=True)
        
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, "GRAND TOTAL:", align='R')
    pdf.cell(50, 10, f"Rs. {t.amount}", ln=True)
    
    out = BytesIO()
    pdf.output(out)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"{t.doc_no}.pdf", mimetype='application/pdf')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
