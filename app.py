from flask import Flask, render_template, request
from models import db
from utils.invoice_generator import generate_invoice

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp.db'

db.init_app(app)

@app.route("/")
def home():
    return "ERP Running 🚀"

@app.route("/create-invoice", methods=["POST"])
def create_invoice():
    client_name = request.form['client']
    items = [{"name": "Service", "price": 1000}]
    gst = 180
    total = 1180

    file = generate_invoice(1, client_name, items, total, gst)

    return f"Invoice Created: {file}"

if __name__ == "__main__":
    app.run()
