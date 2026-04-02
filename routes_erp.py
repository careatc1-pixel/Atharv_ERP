import pandas as pd
import json
from flask import Blueprint, request, redirect, url_for, send_file, session
from io import BytesIO
from fpdf import FPDF
from models import db, Client, Transaction
from datetime import datetime

erp_bp = Blueprint('erp', __name__)

# --- CLIENT MODULE (No Change) ---
@erp_bp.route('/add-client', methods=['POST'])
def add_client():
    c = Client(company=request.form.get('company'), name=request.form.get('name'), 
               contact=request.form.get('contact'), email=request.form.get('email'), 
               address=request.form.get('address'), gstin=request.form.get('gst'))
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('index'))

# --- BILLING MODULE (WITH DYNAMIC GST SLABS) ---
@erp_bp.route('/create-invoice', methods=['POST'])
def create_invoice():
    client_id = request.form['client_id']
    services = request.form.getlist('service[]')
    prices = request.form.getlist('price[]')
    discount = float(request.form.get('discount', 0))
    gst_rate = float(request.form.get('gst_rate', 18)) # Default 18% agar select na ho
    
    items = [{"desc": s, "amt": float(p)} for s, p in zip(services, prices) if s and p]
    subtotal = sum(i['amt'] for i in items)
    taxable_value = subtotal - discount
    
    # Dynamic GST Calculation based on selected slab
    gst_amt = round(taxable_value * (gst_rate / 100), 2)
    grand_total = round(taxable_value + gst_amt)
    
    inv_no = f"ATC/GST/{Transaction.query.filter_by(type='Invoice').count() + 1:03d}"
    
    # Note: Storing gst_rate in items_json or a separate field if needed in future
    t = Transaction(doc_no=inv_no, client_id=client_id, type='Invoice', amount=grand_total, 
                    gst_amt=gst_amt, discount=discount, items_json=json.dumps({"items": items, "rate": gst_rate}))
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('index'))

# --- UPDATED PDF GENERATOR (SLAB WISE) ---
@erp_bp.route('/download-pdf/<int:tid>')
def download_pdf(tid):
    t = Transaction.query.get(tid)
    c = Client.query.get(t.client_id)
    data = json.loads(t.items_json)
    items = data.get('items', [])
    gst_rate = data.get('rate', 18)
    
    # GST Split (CGST + SGST)
    half_rate = gst_rate / 2
    half_amt = round(t.gst_amt / 2, 2)
    taxable = round(t.amount - t.gst_amt, 2)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(26, 26, 46); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 20, "ATHARV TECH CO.", ln=True, align='C')
    pdf.set_font("Arial", '', 10); pdf.cell(190, 5, f"TAX INVOICE - GST @ {gst_rate}%", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.ln(20); pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, f"INVOICE NO: {t.doc_no}"); pdf.cell(90, 10, f"DATE: {t.date.strftime('%d-%m-%Y')}", ln=True, align='R')
    
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(100, 5, "BILL TO:"); pdf.ln(5)
    pdf.set_font("Arial", '', 10); pdf.cell(100, 5, f"{c.company}"); pdf.ln(5); pdf.cell(100, 5, f"GSTIN: {c.gstin}"); pdf.ln(10)
    
    pdf.set_fill_color(235, 235, 235); pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 10, " Description", border=1, fill=True); pdf.cell(50, 10, " Taxable Amt", border=1, ln=True, fill=True, align='R')
    
    pdf.set_font("Arial", '', 10)
    for item in items:
        pdf.cell(140, 10, f" {item['desc']}", border=1)
        pdf.cell(50, 10, f" {item['amt']} ", border=1, ln=True, align='R')
    
    pdf.ln(5)
    pdf.cell(140, 8, f"CGST ({half_rate}%):", align='R'); pdf.cell(50, 8, f"{half_amt}", ln=True, align='R')
    pdf.cell(140, 8, f"SGST ({half_rate}%):", align='R'); pdf.cell(50, 8, f"{half_amt}", ln=True, align='R')
    
    pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 12, "GRAND TOTAL (Rounded):", border='T', align='R')
    pdf.cell(50, 12, f"Rs. {t.amount}", border='T', ln=True, align='R')
    
    out = BytesIO(); pdf.output(out); out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"{t.doc_no}.pdf", mimetype='application/pdf')
