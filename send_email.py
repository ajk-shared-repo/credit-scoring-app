
import smtplib
from email.message import EmailMessage

def send_email_with_pdf(receiver_email, applicant_name, pdf_filename, smtp_server, smtp_port, sender_email, sender_password):
    msg = EmailMessage()
    msg['Subject'] = f"Credit Report for {applicant_name}"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(f"Dear {applicant_name},\n\nAttached is your credit report.\n\nBest regards,\nCredit Team")

    # Attach PDF
    with open(pdf_filename, 'rb') as f:
        pdf_data = f.read()
        msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=pdf_filename)

    # Send the email
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)
