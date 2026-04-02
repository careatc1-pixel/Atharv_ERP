import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from io import BytesIO

app = Flask(__name__)
app.secret_key = "atharv_modular_erp_2026"

# Database Configuration
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Client Model (Detailed)
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))

with app.app_context():
    db.create_all()

ADMIN_EMAIL = "care.atc1@gmail.com"
ADMIN_PASSWORD = "Atharv$321"

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    clients = Client.query.all()
    return render_template('admin.html', clients=clients)

@app.route('/login', methods=['POST'])
def login():
    if request.form['email'] == ADMIN_EMAIL and request.form['password'] == ADMIN_PASSWORD:
        session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- CLIENT MODULE ACTIONS ---

@app.route('/add-client', methods=['POST'])
def add_client():
    c = Client(company=request.form['company'], name=request.form['name'], contact=request.form['contact'], 
               email=request.form['email'], address=request.form['address'], gstin=request.form['gst'])
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/bulk-upload', methods=['POST'])
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

@app.route('/export-excel')
def export_excel():
    clients = Client.query.all()
    data = [{"Company": c.company, "Name": c.name, "Email": c.email, "Contact": c.contact, "GSTIN": c.gstin} for c in clients]
    df = pd.DataFrame(data)
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name="ATC_Client_List.xlsx")

@app.route('/export-pdf')
def export_pdf():
    clients = Client.query.all()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, "ATHARV TECH CO. - CLIENT MASTER LIST", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 10, "Company", 1); pdf.cell(40, 10, "Name", 1); pdf.cell(60, 10, "Email", 1); pdf.cell(40, 10, "Contact", 1, ln=True)
    pdf.set_font("Arial", '', 9)
    for c in clients:
        pdf.cell(50, 10, str(c.company)[:22], 1); pdf.cell(40, 10, str(c.name)[:18], 1)
        pdf.cell(60, 10, str(c.email), 1); pdf.cell(40, 10, str(c.contact), 1, ln=True)
    out = BytesIO()
    pdf.output(out)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name="ATC_Client_List.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
