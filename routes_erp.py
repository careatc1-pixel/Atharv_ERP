import pandas as pd
import json
from flask import Blueprint, request, redirect, url_for, send_file, session
from io import BytesIO
from fpdf import FPDF
from models import db, Client, Transaction
from datetime import datetime

erp_bp = Blueprint('erp', __name__)

@erp_bp.route('/add-client', methods=['POST'])
def add_client():
    c = Client(company=request.form.get('company'), name=request.form.get('name'), 
               contact=request.form.get('contact'), email=request.form.get('email'), 
               address=request.form.get('address'), gstin=request.form.get('gst'))
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('index'))

@erp_bp.route('/bulk-upload', methods=['POST'])
def bulk_upload():
    file = request.files['file']
    if file:
        df = pd.read_excel(file)
        for _, row in df.iterrows():
            if not Client.query.filter_by(email=row['Email']).first():
                c = Client(company=row['Company'], name=row['Name'], contact=row['Contact'], 
                           email=row['Email'], address=row['Address'], gstin=row.get('GSTIN', 'N/A'))
                db.session.add(c)
        db.session.commit()
    return redirect(url_for('index'))

@erp_bp.route('/create-invoice', methods=['POST'])
def create_invoice():
    client_id = request.form['client_id']
    services = request.form.getlist('service[]')
    prices = request.form.getlist('price[]')
    items = [{"desc": s, "amt": float(p)} for s, p in zip(services, prices) if s and p]
    
    subtotal = sum(i['amt'] for i in items)
    discount = float(request.form.get('discount', 0))
    taxable = subtotal - discount
    gst = round(taxable * 0.18, 2)
    grand_total = round(taxable + gst)
    
    inv_no = f"ATC/INV/{Transaction.query.filter_by(type='Invoice').count() + 1:03d}"
    t = Transaction(doc_no=inv_no, client_id=client_id, type='Invoice', amount=grand_total, 
                    gst_amt=gst, discount=discount, items_json=json.dumps(items))
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('index'))

@erp_bp.route('/add-payment', methods=['POST'])
def add_payment():
    rec_no = f"ATC/REC/{Transaction.query.filter_by(type='Payment').count() + 1:03d}"
    t = Transaction(doc_no=rec_no, client_id=request.form['client_id'], type='Payment', 
                    amount=float(request.form['amount']), items_json=json.dumps([{"note": request.form['note']}]))
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('index'))

@erp_bp.route('/download-pdf/<int:tid>')
def download_pdf(tid):
    t = Transaction.query.get(tid)
    c = Client.query.get(t.client_id)
    items = json.loads(t.items_json)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(26, 26, 46); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 20, "ATHARV TECH CO.", ln=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.ln(20); pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, f"{t.type.upper()} NO: {t.doc_no}")
    pdf.cell(90, 10, f"DATE: {t.date.strftime('%d-%m-%Y')}", ln=True, align='R')
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(100, 5, f"BILL TO: {c.company} ({c.name})"); pdf.ln(5)
    pdf.cell(100, 5, f"GSTIN: {c.gstin}"); pdf.ln(10)
    pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 10, " Description", border=1, fill=True); pdf.cell(50, 10, " Amount", border=1, ln=True, fill=True, align='R')
    pdf.set_font("Arial", '', 10)
    for item in items:
        desc = item.get('desc') or item.get('note')
        pdf.cell(140, 10, f" {desc}", border=1); pdf.cell(50, 10, f" {item.get('amt', t.amount)} ", border=1, ln=True, align='R')
    pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(140, 10, "TOTAL AMOUNT:", align='R')
    pdf.cell(50, 10, f"Rs. {t.amount}", ln=True, align='R')
    out = BytesIO(); pdf.output(out); out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"{t.doc_no}.pdf", mimetype='application/pdf')
