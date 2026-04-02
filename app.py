import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
app.secret_key = "atharv_tech_final_safe_key_2026"

# Database Configuration
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Client Model
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    company_name = db.Column(db.String(150))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    project_name = db.Column(db.String(200))
    progress = db.Column(db.Integer, default=0)
    total_bill = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    gst_number = db.Column(db.String(20))

with app.app_context():
    db.create_all()

ADMIN_EMAIL = "care.atc1@gmail.com"
ADMIN_PASSWORD = "Atharv$321"

@app.route('/')
def index(): return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('email') == ADMIN_EMAIL and request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    clients = Client.query.all()
    return render_template('admin.html', clients=clients, now=datetime.now())

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

@app.route('/update-client/<int:id>', methods=['POST'])
def update_client(id):
    client = Client.query.get(id)
    client.progress = request.form.get('progress')
    client.paid_amount = float(request.form.get('paid', 0))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/download-invoice/<int:id>')
def download_invoice(id):
    client = Client.query.get(id)
    gst = round(client.total_bill * 0.18, 2)
    total = round(client.total_bill + gst, 2)
    
    # --- Professional FPDF Design ---
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(26, 26, 46) # Dark Blue
    pdf.cell(200, 10, "ATHARV TECH CO.", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 5, "Software Automation & IT Solutions | Est. 2023", ln=True, align='C')
    pdf.ln(10)
    
    # Invoice Title
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f" TAX INVOICE ", ln=True, align='L', fill=True)
    pdf.ln(5)
    
    # Client Details
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 7, "BILL TO:")
    pdf.cell(100, 7, f"DATE: {datetime.now().strftime('%d-%m-%Y')}", ln=True, align='R')
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 6, f"{client.company_name} ({client.name})")
    pdf.ln(6)
    pdf.cell(100, 6, f"GSTIN: {client.gst_number}")
    pdf.ln(6)
    pdf.multi_cell(100, 6, f"Address: {client.address}")
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(26, 26, 46)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 10, " Description", border=1, fill=True)
    pdf.cell(50, 10, " Amount (Rs.)", border=1, ln=True, fill=True, align='R')
    
    # Table Content
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    pdf.cell(140, 10, f" {client.project_name} Services", border=1)
    pdf.cell(50, 10, f" {client.total_bill} ", border=1, ln=True, align='R')
    
    # Totals
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.cell(140, 8, "Subtotal:", align='R')
    pdf.cell(50, 8, f"Rs. {client.total_bill}", ln=True, align='R')
    pdf.cell(140, 8, "GST (18%):", align='R')
    pdf.cell(50, 8, f"Rs. {gst}", ln=True, align='R')
    
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(15, 52, 96)
    pdf.cell(140, 10, "GRAND TOTAL:", align='R')
    pdf.cell(50, 10, f"Rs. {total}", ln=True, align='R')
    
    # Footer
    pdf.ln(30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(200, 10, "This is a computer generated invoice. No signature required.", ln=True, align='C')

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Invoice_{client.name}.pdf'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
