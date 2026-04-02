from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# Live Server (Render) ke liye Database settings
# Agar hum Render par hain to uska DB use hoga, nahi to local 'atharv_erp.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///atharv_erp.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# Database Table
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    project_name = db.Column(db.String(200))
    progress = db.Column(db.Integer, default=0)

if not os.path.exists('uploads'):
    os.makedirs('uploads')

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    all_clients = Client.query.all()
    return render_template('index.html', clients=all_clients)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and file.filename != '':
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        df = pd.read_excel(filepath)
        for index, row in df.iterrows():
            exists = Client.query.filter_by(email=row['Email']).first()
            if not exists:
                new_client = Client(
                    name=row['Name'], 
                    email=row['Email'], 
                    project_name=row.get('Project', 'General')
                )
                db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Local testing ke liye port 5000, Live ke liye automatic port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
