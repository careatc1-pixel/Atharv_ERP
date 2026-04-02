import os
from flask import Flask, render_template, session, redirect, url_for, request
from models import db, Client, Transaction
from routes_erp import erp_bp

app = Flask(__name__)
app.secret_key = "atharv_pro_v4_2026"

current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(current_dir, 'atharv_erp.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(erp_bp)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    clients = Client.query.all()
    txs = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('admin.html', clients=clients, txs=txs)

@app.route('/login', methods=['POST'])
def login():
    if request.form['email'] == "care.atc1@gmail.com" and request.form['password'] == "Atharv$321":
        session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
