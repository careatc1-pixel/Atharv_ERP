from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

# Render ke liye folder path set karna
current_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(current_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "atharv_secret_key"

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    clients = Client.query.all()
    return render_template('admin.html', clients=clients)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and file.filename != '':
        df = pd.read_excel(file)
        for _, row in df.iterrows():
            if not Client.query.filter_by(email=row['Email']).first():
                new_client = Client(
                    name=row['Name'], 
                    email=row['Email'], 
                    project_name=row.get('Project', 'N/A'),
                    total_bill=row.get('Bill', 0)
                )
                db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update/<int:id>', methods=['POST'])
def update_client(id):
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
    return "Email not found! Please contact Atharv Tech Co."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
