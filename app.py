import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from io import BytesIO

app = Flask(__name__)
app.secret_key = "atharv_tech_client_module_2026"

# Database
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
db = SQLAlchemy(app)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    company = db.Column(db.String(150))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))

with app.app_context(): db.create_all()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    clients = Client.query.all()
    return render_template('admin.html', clients=clients)

@app.route('/login', methods=['POST'])
def login():
    if request.form['email'] == "care.atc1@gmail.com" and request.form['password'] == "Atharv$321":
        session['logged_in'] = True
    return redirect(url_for('index'))

# --- CLIENT ACTIONS ---

@app.route('/add-client', methods=['POST'])
def add_client():
    c = Client(name=request.form['name'], company=request.form['company'], contact=request.form['contact'], email=request.form['email'], address=request.form['address'], gstin=request.form['gst'])
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
                c = Client(name=row['Name'], company=row['Company'], contact=row['Contact'], email=row['Email'], address=row['Address'], gstin=row.get('GSTIN', 'N/A'))
                db.session.add(c)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/export-excel')
def export_excel():
    clients = Client.query.all()
    data = [{"Name": c.name, "Company": c.company, "Email": c.email, "Contact": c.contact, "GSTIN": c.gstin} for c in clients]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Clients')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="Client_List.xlsx")

@app.route('/export-pdf')
def export_pdf():
    clients = Client.query.all()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, "ATHARV TECH CO. - CLIENT LIST", ln=True, align='C')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Company", border=1)
    pdf.cell(40, 10, "Name", border=1)
    pdf.cell(60, 10, "Email", border=1)
    pdf.cell(50, 10, "Contact", border=1, ln=True)
    pdf.set_font("Arial", '', 9)
    for c in clients:
        pdf.cell(40, 10, str(c.company)[:20], border=1)
        pdf.cell(40, 10, str(c.name)[:20], border=1)
        pdf.cell(60, 10, str(c.email), border=1)
        pdf.cell(50, 10, str(c.contact), border=1, ln=True)
    
    out = BytesIO()
    pdf.output(out)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name="Client_List.pdf", mimetype='application/pdf')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
