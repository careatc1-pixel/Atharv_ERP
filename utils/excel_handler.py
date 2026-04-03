import pandas as pd

def export_clients_to_excel(Client):
    clients = Client.query.all()
    data = []

    for c in clients:
        data.append({
            "Name": c.name,
            "Email": c.email,
            "Phone": c.phone
        })

    file_path = "clients.xlsx"
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    return file_path


def upload_clients_from_excel(file, Client, db):
    df = pd.read_excel(file)

    for _, row in df.iterrows():
        client = Client(
            name=row['name'],
            email=row['email'],
            phone=row['phone']
        )
        db.session.add(client)

    db.session.commit()
