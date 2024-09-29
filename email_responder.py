import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Credentials are stored in GitHub Secrets
username = os.getenv("EMAIL_USERNAME")  # Set in GitHub Secrets
password = os.getenv("EMAIL_PASSWORD")  # Set in GitHub Secrets
imap_server = os.getenv("IMAP_SERVER")  # IMAP server address (e.g., "imap.gmail.com")
smtp_server = os.getenv("SMTP_SERVER")  # SMTP server address (e.g., "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", 587))  # Default SMTP port

# Function to check inbox for new replies
def check_inbox():
    try:
        logging.info("Connecting to IMAP server...")
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        mail.select("inbox")
        logging.info("Connected to inbox.")

        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK":
            logging.error(f"Failed to retrieve messages: {status}")
            return
        
        messages = messages[0].split()
        logging.info(f"Found {len(messages)} unread messages.")

        for mail_id in messages:
            status, msg_data = mail.fetch(mail_id, "(RFC822)")
            if status != "OK":
                logging.error(f"Failed to fetch email ID {mail_id}: {status}")
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or 'utf-8')

                    from_ = msg.get("From")
                    logging.info(f"New email from {from_} with subject {subject}")

                    # If the email has multiple parts, get the text part
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                logging.info(f"Email body: {body}")
                                response_content = ai_generate_response(subject, body)
                                send_email_response(from_, subject, response_content)
                                # Mark the email as read
                                mail.store(mail_id, '+FLAGS', '\\Seen')
                    else:
                        body = msg.get_payload(decode=True).decode()
                        logging.info(f"Email body: {body}")
                        response_content = ai_generate_response(subject, body)
                        send_email_response(from_, subject, response_content)
                        # Mark the email as read
                        mail.store(mail_id, '+FLAGS', '\\Seen')

        mail.close()
        mail.logout()
        logging.info("Disconnected from IMAP server.")
    
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP error: {e}")
    except ConnectionRefusedError as e:
        logging.error(f"Connection refused: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Dummy AI function for now (replace with OpenRouter call)
def ai_generate_response(subject, original_email_body):
    logging.info(f"Generating AI response for subject: {subject}")
    return f"Thank you for your response about '{subject}'. Here's a follow-up."

# Send email response
def send_email_response(recipient_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = f"Re: {subject}"
    msg["From"] = username
    msg["To"] = recipient_email

    try:
        logging.info(f"Sending email response to {recipient_email}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, recipient_email, msg.as_string())
            logging.info(f"Response sent to {recipient_email}")
    except smtplib.SMTPException as e:
        logging.error(f"Failed to send email: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending email: {e}")

# Check inbox once (this will be triggered by GitHub Actions)
if __name__ == "__main__":
    check_inbox()
