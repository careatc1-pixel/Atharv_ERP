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

# --- ADMIN LOGIN/LOGOUT ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "<h3>Invalid Admin Credentials</h3><a href='/login'>Try Again</a>"
    return render_template('login.html')

# --- CLIENT LOGIN/LOGOUT ---
@app.route('/client-login', methods=['POST'])
def client_login():
    email = request.form.get('email')
    client = Client.query.filter_by(email=email).first()
    if client:
        session['client_id'] = client.id
        return redirect(url_for('client_dashboard'))
    return "<h3>Email Not Registered!</h3><a href='/'>Back to Home</a>"

@app.route('/client-dashboard')
def client_dashboard():
    if 'client_id' not in session:
        return redirect(url_for('index'))
    client = Client.query.get(session['client_id'])
    return render_template('client_view.html', client=client)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- ADMIN PROTECTED ROUTES ---
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
    name, email = request.form.get('name'), request.form.get('email')
    project, bill = request.form.get('project'), request.form.get('bill', 0)
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
