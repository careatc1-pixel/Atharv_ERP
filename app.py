import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
app.secret_key = "atharv_tech_exclusive_2026"

# Database Config
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

db = SQLAlchemy(app)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    company_name = db.Column(db.String(150))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    project_name = db.Column(db.String(200))
    total_bill = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    gst_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

ADMIN_EMAIL = "care.atc1@gmail.com"
ADMIN_PASSWORD = "Atharv$321"

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('email') == ADMIN_EMAIL and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    clients = Client.query.all()
    return render_template('admin.html', clients=clients)

@app.route('/add-client', methods=['POST'])
def add_client():
    new_c = Client(
        name=request.form.get('name'), company_name=request.form.get('company'),
        contact=request.form.get('contact'), email=request.form.get('email'),
        address=request.form.get('address'), project_name=request.form.get('project'),
        total_bill=float(request.form.get('bill', 0)), gst_number=request.form.get('gst', 'N/A')
    )
    db.session.add(new_c)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update-payment/<int:id>', methods=['POST'])
def update_payment(id):
    client = Client.query.get(id)
    client.paid_amount = float(request.form.get('paid', 0))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/download-invoice/<int:id>')
def download_invoice(id):
    client = Client.query.get(id)
    gst = round(client.total_bill * 0.18, 2)
    total = round(client.total_bill + gst, 2)
    
    pdf = FPDF()
    pdf.add_page()
    # Design High Class
    pdf.set_fill_color(26, 26, 46)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(190, 25, "ATHARV TECH CO.", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(100, 10, "TAX INVOICE")
    pdf.set_font("Arial", '', 10)
    pdf.cell(90, 10, f"Date: {datetime.now().strftime('%d-%b-%Y')}", ln=True, align='R')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 7, "BILL TO:")
    pdf.ln(7)
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 6, f"Company: {client.company_name}")
    pdf.ln(6)
    pdf.cell(100, 6, f"Contact: {client.name} | {client.contact}")
    pdf.ln(6)
    pdf.cell(100, 6, f"GSTIN: {client.gst_number}")
    pdf.ln(6)
    pdf.multi_cell(100, 6, f"Address: {client.address}")
    
    pdf.ln(10)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " Description", border=1, fill=True)
    pdf.cell(50, 10, " Amount (INR)", border=1, ln=True, fill=True, align='R')
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(140, 12, f" {client.project_name} Execution", border=1)
    pdf.cell(50, 12, f" {client.total_bill} ", border=1, ln=True, align='R')
    
    pdf.ln(5)
    pdf.cell(140, 8, "Subtotal:", align='R')
    pdf.cell(50, 8, f"{client.total_bill}", ln=True, align='R')
    pdf.cell(140, 8, "GST (18%):", align='R')
    pdf.cell(50, 8, f"{gst}", ln=True, align='R')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(140, 12, "GRAND TOTAL:", align='R')
    pdf.cell(50, 12, f"Rs. {total}", ln=True, align='R')

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Invoice_{client.company_name}.pdf'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
