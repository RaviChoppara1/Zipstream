import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import datetime

def get_current_date():
    return datetime.datetime.now().strftime('%d%m%Y')

def get_csv_files():
    current_date = get_current_date()
    logs_folder = os.path.join('logs', current_date)
    csv_files = []
    for root, dirs, files in os.walk(logs_folder):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    return csv_files

def send_email_with_dynamic_csv(sender_email, sender_password, receiver_email, subject, body):
    csv_files = get_csv_files()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    # Attach body to the email
    message.attach(MIMEText(body, 'plain'))

    # Attach CSV files
    for csv_file_path in csv_files:
        attachment = MIMEBase('application', 'octet-stream')
        with open(csv_file_path, 'rb') as file:
            attachment.set_payload(file.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename={os.path.basename(csv_file_path)}')
        message.attach(attachment)

    # Connect to SMTP server and send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())

# Example usage:
# sender_email = 'your_email@example.com'
# sender_password = 'your_password'
# receiver_email = 'recipient@example.com'
# subject = 'CSV Files Attachment'
# body = 'Please find the attached CSV files.'
#
# send_email_with_dynamic_csv(sender_email, sender_password, receiver_email, subject, body)
