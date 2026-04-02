from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(current_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "atharv_tech_super_secret_key" 

# Database Settings
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Table
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    project_name = db.Column(db.String(200))
    progress = db.Column(db.Integer, default=0)
    total_bill = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

# --- ADMIN CREDENTIALS ---
ADMIN_EMAIL = "care.atc1@gmail.com"
ADMIN_PASSWORD = "Atharv$321"

@app.route('/')
def index():
    return render_template('index.html')

# Login Page Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "<h3 style='color:red; text-align:center;'>Galt Details! Sahi Email/Password dalein.</h3><br><center><a href='/login'>Wapas Jayein</a></center>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# Protected Admin Dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    clients = Client.query.all()
    return render_template('admin.html', clients=clients)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    file = request.files['file']
    if file and file.filename != '':
        df = pd.read_excel(file)
        for _, row in df.iterrows():
            if not Client.query.filter_by(email=row['Email']).first():
                new_client = Client(name=row['Name'], email=row['Email'], project_name=row.get('Project', 'N/A'), total_bill=row.get('Bill', 0))
                db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/add-single', methods=['POST'])
def add_single():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name')
    email = request.form.get('email')
    project = request.form.get('project')
    bill = request.form.get('bill', 0)
    if not Client.query.filter_by(email=email).first():
        new_client = Client(name=name, email=email, project_name=project, total_bill=bill)
        db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update/<int:id>', methods=['POST'])
def update_client(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    client = Client.query.get(id)
    client.progress = request.form.get('progress')
    client.paid_amount = request.form.get('paid')
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/client-check', methods=['POST'])
def client_check():
    email = request.form.get('email')
    client = Client.query.filter_by(email=email).first()
    if client:
        return render_template('client_view.html', client=client)
    return "<h1>Email Nahi Mila! Atharv Tech Co. se sampark karein.</h1><a href='/'>Wapas</a>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
