import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
app.secret_key = "atharv_tech_final_safe_key"

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
    name = db.Column(db.String(100), nullable=False)
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
        name=request.form.get('name'),
        company_name=request.form.get('company'),
        contact=request.form.get('contact'),
        email=request.form.get('email'),
        address=request.form.get('address'),
        project_name=request.form.get('project'),
        total_bill=float(request.form.get('bill', 0)),
        gst_number=request.form.get('gst', 'N/A')
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
    gst_amt = round(client.total_bill * 0.18, 2)
    grand_total = client.total_bill + gst_amt
    
    # FPDF logic to create Invoice
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "TAX INVOICE - Atharv Tech Co.", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Client: {client.company_name}", ln=True)
    pdf.cell(200, 10, f"Address: {client.address}", ln=True)
    pdf.cell(200, 10, f"GSTIN: {client.gst_number}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, f"Project: {client.project_name}", ln=True)
    pdf.cell(200, 10, f"Base Amount: Rs. {client.total_bill}", ln=True)
    pdf.cell(200, 10, f"GST (18%): Rs. {gst_amt}", ln=True)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"Total Amount: Rs. {grand_total}", ln=True)
    
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
