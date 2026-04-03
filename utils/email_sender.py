import smtplib
from email.mime.text import MIMEText

def send_payment_reminder(to_email, client_name, amount):
    msg = MIMEText(f"Dear {client_name},\n\nPlease pay pending amount ₹{amount}")
    msg['Subject'] = "Payment Reminder"
    msg['From'] = "your_email@gmail.com"
    msg['To'] = to_email

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("your_email@gmail.com", "your_app_password")

    server.send_message(msg)
    server.quit()
