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
    gst_rate = float(request.form.get('gst_rate', 18))
    discount = float(request.form.get('discount', 0))
    
    items = [{"desc": s, "amt": float(p)} for s, p in zip(services, prices) if s and p]
    subtotal = sum(i['amt'] for i in items)
    taxable = subtotal - discount
    gst_val = round(taxable * (gst_rate / 100), 2)
    total = round(taxable + gst_val)
    
    inv_no = f"ATC/GST/{Transaction.query.filter_by(type='Invoice').count() + 1:03d}"
    t = Transaction(doc_no=inv_no, client_id=client_id, type='Invoice', amount=total, 
                    gst_amt=gst_val, discount=discount, items_json=json.dumps({"items": items, "rate": gst_rate}))
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('index'))

@erp_bp.route('/download-pdf/<int:tid>')
def download_pdf(tid):
    t = Transaction.query.get(tid)
    c = Client.query.get(t.client_id)
    data = json.loads(t.items_json)
    items = data.get('items', [])
    rate = data.get('rate', 18)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(26, 26, 46); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 20, "ATHARV TECH CO.", ln=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.ln(20); pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, f"INV: {t.doc_no}"); pdf.cell(90, 10, f"DATE: {t.date.strftime('%d-%m-%Y')}", ln=True, align='R')
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(100, 5, f"BILL TO: {c.company}"); pdf.ln(5)
    pdf.set_font("Arial", '', 10); pdf.cell(100, 5, f"GSTIN: {c.gstin}"); pdf.ln(10)
    pdf.set_fill_color(240, 240, 240); pdf.cell(140, 10, " Description", 1, 0, 'L', True); pdf.cell(50, 10, " Amt", 1, 1, 'R', True)
    for i in items:
        pdf.cell(140, 10, f" {i['desc']}", 1); pdf.cell(50, 10, f" {i['amt']} ", 1, 1, 'R')
    pdf.ln(5); pdf.cell(140, 8, f"GST ({rate}%):", align='R'); pdf.cell(50, 8, f"{t.gst_amt}", ln=True, align='R')
    pdf.set_font("Arial", 'B', 12); pdf.cell(140, 10, "TOTAL:", align='R'); pdf.cell(50, 10, f"Rs. {t.amount}", ln=True, align='R')
    out = BytesIO(); pdf.output(out); out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"{t.doc_no}.pdf", mimetype='application/pdf')
