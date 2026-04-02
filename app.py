from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(current_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "atharv_tech_premium_secret"

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

ADMIN_EMAIL = "care.atc1@gmail.com"
ADMIN_PASSWORD = "Atharv$321"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/client-login', methods=['POST'])
def client_login():
    email = request.form.get('email')
    client = Client.query.filter_by(email=email).first()
    if client:
        session['client_id'] = client.id
        return redirect(url_for('client_dashboard'))
    return "<h3>Email Not Found!</h3><a href='/'>Back</a>"

@app.route('/client-dashboard')
def client_dashboard():
    if 'client_id' not in session: return redirect(url_for('index'))
    client = Client.query.get(session['client_id'])
    return render_template('client_view.html', client=client)

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    clients = Client.query.all()
    # Stats for Dashboard
    total_clients = len(clients)
    total_revenue = sum(c.total_bill for c in clients)
    pending_payments = sum(c.total_bill - c.paid_amount for c in clients)
    return render_template('admin.html', clients=clients, t_c=total_clients, t_r=total_revenue, p_p=pending_payments)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Actions
@app.route('/add-single', methods=['POST'])
def add_single():
    new_client = Client(
        name=request.form.get('name'),
        email=request.form.get('email'),
        project_name=request.form.get('project'),
        total_bill=float(request.form.get('bill', 0))
    )
    db.session.add(new_client)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update-progress/<int:id>', methods=['POST'])
def update_progress(id):
    client = Client.query.get(id)
    client.progress = request.form.get('progress')
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update-payment/<int:id>', methods=['POST'])
def update_payment(id):
    client = Client.query.get(id)
    client.paid_amount = float(request.form.get('paid', 0))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
