import pandas as pd
from models import Client, db

def upload_clients_from_excel(file):
    df = pd.read_excel(file)

    for _, row in df.iterrows():
        client = Client(
            name=row['name'],
            email=row['email'],
            phone=row['phone']
        )
        db.session.add(client)

    db.session.commit()
