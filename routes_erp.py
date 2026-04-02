class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))
