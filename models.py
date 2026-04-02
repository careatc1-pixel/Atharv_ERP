from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doc_no = db.Column(db.String(50), unique=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    type = db.Column(db.String(20)) # 'Invoice' or 'Payment'
    amount = db.Column(db.Float)
    gst_amt = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    items_json = db.Column(db.Text) 
    date = db.Column(db.DateTime, default=datetime.utcnow)
