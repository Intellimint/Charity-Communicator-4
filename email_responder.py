import imaplib
import email
from email.header import decode_header
import time
import smtplib
from email.mime.text import MIMEText
import os

# Credentials are stored in GitHub Secrets
username = os.getenv("EMAIL_USERNAME")  # Set in GitHub Secrets
password = os.getenv("EMAIL_PASSWORD")  # Set in GitHub Secrets
imap_server = os.getenv("IMAP_SERVER")  # IMAP server address (e.g., "imap.gmail.com")
smtp_server = os.getenv("SMTP_SERVER")  # SMTP server address (e.g., "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", 587))  # Default SMTP port

# Function to check inbox for new replies
def check_inbox():
    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(username, password)
    mail.select("inbox")
    
    # Search for unread emails
    status, messages = mail.search(None, 'UNSEEN')
    messages = messages[0].split()

    for mail_id in messages:
        status, msg_data = mail.fetch(mail_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding)

                from_ = msg.get("From")
                print(f"New email from {from_} with subject {subject}")

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            print(f"Email body: {body}")
                            response_content = ai_generate_response(subject, body)
                            send_email_response(from_, subject, response_content)
                            mail.store(mail_id, '+FLAGS', '\\Seen')
                else:
                    body = msg.get_payload(decode=True).decode()
                    response_content = ai_generate_response(subject, body)
                    send_email_response(from_, subject, response_content)
                    mail.store(mail_id, '+FLAGS', '\\Seen')

    mail.close()
    mail.logout()

# Dummy AI function for now (replace with OpenRouter call)
def ai_generate_response(subject, original_email_body):
    return f"Thank you for your response about '{subject}'. Here's a follow-up."

# Send email response
def send_email_response(recipient_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = f"Re: {subject}"
    msg["From"] = username
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, recipient_email, msg.as_string())
            print(f"Response sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Check inbox once (this will be triggered by GitHub Actions)
if __name__ == "__main__":
    check_inbox()
