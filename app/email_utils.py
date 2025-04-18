import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage

def send_email(to, subject, message):
    sender_email = os.getenv('MAIL_USERNAME')
    sender_password = os.getenv('MAIL_PASSWORD')  # App password from Gmail

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

def send_otp_email(recipient_email, otp_code):
    msg = EmailMessage()
    msg['Subject'] = 'Your OTP for Flat Maintenance Tracker'
    msg['From'] = os.getenv('MAIL_USERNAME')
    msg['To'] = recipient_email
    msg.set_content(f'Your OTP for signup is: {otp_code}')

    with smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT'))) as smtp:
        smtp.starttls()
        smtp.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
        smtp.send_message(msg)