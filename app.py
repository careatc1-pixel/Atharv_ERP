from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from io import BytesIO
from xhtml2pdf import pisa
from datetime import datetime

current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(current_dir, 'templates'))
app.secret_key = "atharv_tech_ultra_pro"

# Database Settings
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Detailed Client & Billing Model
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

# --- HELPER: PDF GENERATOR ---
def render_pdf(template_src, context_dict):
    html = render_template(template_src, **context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

# --- ROUTES ---
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

# Add Detailed Client
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

# Generate Invoice/Receipt PDF
@app.route('/download-invoice/<int:id>')
def download_invoice(id):
    client = Client.query.get(id)
    gst_amt = client.total_bill * 0.18 # 18% GST calculation
    grand_total = client.total_bill + gst_amt
    data = {'client': client, 'gst': gst_amt, 'total': grand_total, 'date': datetime.now().strftime('%d-%m-%Y')}
    pdf = render_pdf('invoice_pdf.html', data)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Invoice_{client.name}.pdf'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
