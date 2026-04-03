from flask import Flask, render_template, request, send_file, redirect
from flask_sqlalchemy import SQLAlchemy
from utils.invoice_generator import generate_invoice
from utils.excel_handler import export_clients_to_excel, upload_clients_from_excel

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp.db'
app.config['SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)

# ================= MODELS =================

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100))
    amount = db.Column(db.Float)

# ================= ROUTES =================

@app.route("/")
def home():
    clients = Client.query.all()
    return render_template("admin.html", clients=clients)

# -------- ADD CLIENT --------
@app.route("/add-client", methods=["POST"])
def add_client():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']

    client = Client(name=name, email=email, phone=phone)
    db.session.add(client)
    db.session.commit()

    return redirect("/")

# -------- EXPORT CLIENTS --------
@app.route("/export-clients")
def export_clients():
    file_path = export_clients_to_excel(Client)
    return send_file(file_path, as_attachment=True)

# -------- UPLOAD EXCEL --------
@app.route("/upload-excel", methods=["POST"])
def upload_excel():
    file = request.files['file']
    upload_clients_from_excel(file, Client, db)
    return redirect("/")

# -------- CREATE INVOICE --------
@app.route("/create-invoice/<int:id>")
def create_invoice(id):
    client = Client.query.get(id)

    items = [{"name": "Service", "price": 1000}]
    gst = 180
    total = 1180

    file = generate_invoice(id, client.name, items, total, gst)

    return send_file(file, as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
